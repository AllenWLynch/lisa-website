import logging
import os, sys
import subprocess
#from logging.handlers import RotatingFileHandler, FileHandler
from logging import FileHandler
import time
import pandas as pd
import numpy as np
import re
import glob

from flask import Flask, render_template, redirect, url_for, send_from_directory, abort
from flask import make_response, jsonify
import json

from flask import request
from flask_bootstrap import Bootstrap
from werkzeug.utils import secure_filename
from celery import Celery
import random
from flask import flash
#from .mail import send_localhost_mail
from flask_httpauth import HTTPBasicAuth,HTTPDigestAuth
import zipfile
import configparser

# initialize an application
app = Flask(__name__, instance_relative_config = True)
app.config['CELERY_BROKER_URL'] = 'redis://localhost:6379/0'
app.config['CELERY_RESULT_BACKEND'] = 'redis://localhost:6379/0'
app.config['JSON_AS_ASCII'] = False
celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)

from .form import LISAForm

app.secret_key = 's3cr3t' # crsf

CONFIG = configparser.ConfigParser()
CONFIG.read('config.ini')

README = '''
Hello! Thank you trying out LISA. With the new website there are new results formats.

Your top regulatory factors can be found in the ".lisa.tsv" tabular results file, while interesting model metadata are in ".metadata.json".
We will be updating the website in the future with new data analysis tools for LISA, so if you want to check back on your results, use:

{site}{url}

For all your data analysis questions, please refer to our guide at 

https://github.com/liulab-dfci/lisa2/blob/master/docs/DataAnalysisGuide.md
'''

# debug mode on
app.debug = False

if not app.debug:
    app.logger.setLevel(logging.DEBUG)
    #handler = RotatingFileHandler(dir_prefix + '/lisa.log', maxBytes=10000000, backupCount=20)
    handler = FileHandler(CONFIG.get('paths','root') + '/lisa.log')
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s: %(message)s")
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(formatter)
    app.logger.addHandler(handler)


class FormValidationError(Exception):
    pass

class GeneListInvalidError(FormValidationError):
    pass

def validate_genelist(gene_str, min_genes = 20, max_genes = 500, error_msg = 'User must provide between {} and {} {} genes.', genelist_type = 'query'):

    genes = [x.strip() for x in gene_str.split('\n') if not x == '']
    #check_available_genes(genes, species)
    app.logger.info("valid gene number %s %s" % (len(genes), genes))
    
    if len(genes) < min_genes or len(genes) > max_genes:
        raise GeneListInvalidError(error_msg.format(str(min_genes), str(max_genes), genelist_type))
    else:
        return genes

@app.errorhandler(500)
def internal_error(exception):
    app.logger.exception(exception)
    return "Sorry internal program error", 500

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.route('/', methods=['GET', 'POST'])
def submit_lisa():
    form = LISAForm()
    app.logger.info(form.validate_on_submit())
    if form.validate_on_submit():

        try:

            to_user = form.mail.data

            geneset = form.genes.data
            geneset = validate_genelist(geneset)
            label = form.labels.data.replace(' ', '_').replace(',','.')
            label = 'gene_set_1' if label == '' else label

            geneset_2 = form.genes2.data
            label_2 = form.labels2.data.replace(' ', '_').replace(',','.')
            label_2 = 'gene_set_2' if label_2 == '' else label_2
            run_two_lists = geneset_2 != ''

            job_name = form.name.data.replace(' ', '_').replace('(', '').replace(')', '').replace('#', '').replace("\'", "").replace('-', '').replace('&', '').replace(',','.')  # user input weird character 
            if job_name == '':
                raise FormValidationError('Please specify a job name')

            isd_method = form.method.data

            species = form.species.data.encode('utf-8')

            rand_id = int(random.random() * 1000)
            prefix = str(job_name) + '_' + secure_filename(time.strftime('%Y-%m-%d-%H:%M:%S', time.localtime())) + '-' + str(rand_id)

            background = form.background.data    
            if background == '':
                background_strategy = 'regulatory'
                background_genes = []
            else:
                background_strategy = 'provided'
                background_genes = validate_genelist(background, len(geneset_1) + 1, 2000, genelist_type='background')

            if run_two_lists:

                if label == label_2:
                    raise FormValidationError('Two lists may not have the same label.')
                
                geneset_2 = validate_genelist(geneset_2)

                redir_url = url_for('show_comparelist_results', task_id = prefix, label_1 = label, label_2 = label_2)

                set_up_folders(prefix, redir_url)

                task = multiple_run_lisa.apply_async(args=(species, geneset, geneset_2, 
                        isd_method, to_user, prefix, label, label_2), countdown=1, expires=3600)

            else:

                redir_url = url_for('show_onelist_results', task_id = prefix, label = label)

                set_up_folders(prefix, redir_url)

                task = run_lisa.apply_async(args=(species, geneset, isd_method, background_strategy, background_genes, to_user, prefix, label), countdown=1, expires=3600)
            
            return redirect(redir_url)

        except FormValidationError as err:
            return render_template('index.html', form = form, message=str(err))

    else:
        return render_template('index.html', form = form, message="")

def get_task_folder(task_id):
    return os.path.join(CONFIG.get('paths','root'), CONFIG.get('paths','upload'), task_id)

def get_task_filepath(task_id, filename):
    return os.path.join(get_task_folder(task_id), filename)

def is_valid_task(task_id):
    return os.path.isdir(os.path.join(CONFIG.get('paths','root'), CONFIG.get('paths','upload'), task_id))

def set_up_folders(prefix, results_url):

    os.mkdir(get_task_folder(prefix))

    with open(get_task_filepath(prefix, 'README.txt'), 'w') as f:
        f.write(README.format(url = results_url, site = CONFIG.get('site','site')))

def run_lisa_command(cmd_args, run_folder):
    try:
        progress = open(os.path.join(run_folder, 'progress.txt'), 'w')

        process = subprocess.call(cmd_args, stderr=progress, 
            env = {"PATH" : CONFIG.get('paths', 'lisa_env')})
       
        return process == 0
        
    finally:
        progress.close()

def compress_files(filenames, destination):

    with zipfile.ZipFile(destination, mode = 'w') as zip_dest:
        for f in filenames + [os.path.join(os.path.dirname(filenames[0]), 'README.txt')]:
            zip_dest.write(f, os.path.basename(f), zipfile.ZIP_DEFLATED)

def post_process_results(run_folder, prefix, labels):

    results_files = [os.path.join(run_folder, label + '.lisa.tsv') for label in labels]
    metadata_files = [os.path.join(run_folder, label + '.metadata.json') for label in labels]

    compress_files(results_files + metadata_files,  os.path.join(CONFIG.get('paths','root'), CONFIG.get('paths','download'), prefix + '.zip'))

    return results_files, metadata_files

@celery.task(bind=True)
def multiple_run_lisa(self, species, geneset_1, geneset_2, isd_method, to_user, prefix, label_1, label_2):

    run_folder = get_task_folder(prefix)

    genelist_files = get_task_filepath(prefix, label_1), get_task_filepath(prefix, label_2)

    with open(genelist_files[0], 'w') as list1:
        list1.write('\n'.join(geneset_1))

    with open(genelist_files[1],'w') as list2:
        list2.write('\n'.join(geneset_2))

    cmd_args = ['lisa','multi',species, genelist_files[0], genelist_files[1], '-b', '501', '-o', run_folder + '/','--save_metadata']

    if not isd_method == 'chipseq':
        cmd_args = cmd_args + ['--use_motifs']

    if run_lisa_command(cmd_args, run_folder):        
        post_process_results(run_folder, prefix, [label_1, label_2])

        
@celery.task(bind=True)
def run_lisa(self, species, query_genes, isd_method, background_strategy, background_genes, to_user, prefix, label):
    
    run_folder = get_task_folder(prefix)

    QUERY_LIST = os.path.join(run_folder, 'query_genes.txt')
    with open(QUERY_LIST, 'w') as f:
        f.write('\n'.join(query_genes))
    
    cmd_args = ['lisa','oneshot',species, QUERY_LIST, '-b', '501', '-o',os.path.join(run_folder, label),'--background_strategy',background_strategy,'--save_metadata']

    if len(background_genes) > 0:
        BACKGROUND_LIST = os.path.join(run_folder, 'background_genes.txt')
        with open(BACKGROUND_LIST, 'w') as f:
            f.write('\n'.join(background_genes))
        cmd_args = cmd_args + ['--background_list', BACKGROUND_LIST]

    if not isd_method == 'chipseq':
        cmd_args = cmd_args + ['--use_motifs']

    app.logger.info(' '.join(cmd_args))

    if run_lisa_command(cmd_args, run_folder):
        post_process_results(run_folder, prefix, (label, ))
        

def track_progress(task_id, num_steps, cheat = True):

    response = dict(status = '0%', state = 'QUEUED')

    try:

        progress_file = get_task_filepath(task_id, 'progress.txt')

        with open(progress_file, 'r') as f:

            response['state'] = 'RUNNING'
            content = f.readlines()
            if len(content) > 0:
                if 'ERROR' in content[-1]:
                    response['state'] = 'ERROR'
                    response['status'] = content[-1]
                else:
                    num_lines = len(content)
                    response['status'] = str(int(num_lines * 100 / num_steps)) + '%'
                    if num_lines >= num_steps:
                        response['state'] = 'DONE'

            elif cheat:
                response['status'] = '50%'
        
        return jsonify(response)

    except IOError:

        if not is_valid_task(task_id):

            response['state'] = 'TASK DNE'
            response['status'] = 'Task with id {} does not exist'.format(task_id)

        return jsonify(response)

def dataframe_to_json(dataframe):
    return json.dumps(dataframe.to_dict(orient = 'records'))


@app.route('/onelist/<task_id>/<label>')
def show_onelist_results(task_id, label):

    return render_template('onelist.html',
        task_id = task_id,
        label = label,
        results = url_for('get_summary_table', task_id = task_id, label = label)
    )

@app.route('/comparelists/<task_id>/<label_1>,<label_2>')
def show_comparelist_results(task_id, label_1, label_2):

    return render_template('comparelists.html',
        task_id = task_id,
        label_1 = label_1,
        label_2 = label_2,
        results_1 = url_for('get_summary_table', task_id = task_id, label = label_1),
        results_2 = url_for('get_summary_table', task_id = task_id, label = label_2),
        joined_results = url_for('compute_joined_dataframe', task_id = task_id, label_1 = label_1, label_2 = label_2),
    )

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.route('/lisa_onelist_status/<task_id>/<label>', methods=['GET', 'POST'])
def lisa_onelist_status(task_id, label):

    if os.path.isfile(get_task_filepath(task_id, label + '.lisa.tsv')):
        return jsonify(dict(status = '100%', state = 'DONE'))
    else:
        return track_progress(task_id, 27)
    
@app.route('/lisa_compare_status/<task_id>/<label_1>,<label_2>', methods=['GET', 'POST'])
def lisa_compare_status(task_id, label_1, label_2):

    if os.path.isfile(get_task_filepath(task_id, label_1 + '.lisa.tsv')) and os.path.isfile(get_task_filepath(task_id, label_2 + '.lisa.tsv')):
        return jsonify(dict(status = '100%', state = 'DONE'))
    else:
        return track_progress(task_id, 10)

@app.route('/stats', methods=['GET'])
def get_stats():
    return render_template('stat.html')

@app.route('/doc', methods=['GET'])
def get_docs():
    return redirect("https://github.com/liulab-dfci/lisa2/blob/master/docs/DataAnalysisGuide.md")

@app.route('/github', methods = ['GET'])
def get_github():
    return redirect("https://github.com/liulab-dfci/lisa2")


@app.route('/gallery/tables/<species>', methods = ['GET'])
def get_gallery_table(species):

    try:
        with open(CONFIG.get('paths','gallery_metadata').format(species = species), 'r') as m:
            metadata = json.load(m)

    except IOError:
        return render_template('404.html'), 404

    return_table = []
    for example_metadata in metadata:

        task_id = species + '_gallery_example_' + example_metadata['id']['text']

        if is_valid_task(task_id):
        
            factor = example_metadata['Factor Perturbed']['text']

            example_metadata['Geneset 1'] = dict(
                text = factor + ' up-regulated genes',
                link = url_for('get_file', task_id = task_id, filename = factor + '_Up-regulated')
            )

            example_metadata['Geneset 2'] = dict(
                text = factor + ' down-regulated genes',
                link = url_for('get_file', task_id = task_id, filename = factor + '_Down-regulated')
            )

            example_metadata['Results'] = dict(
                text = factor + ' results',
                link = url_for('show_comparelist_results',
                    task_id = task_id,
                    label_1 = factor + '_Up-regulated',
                    label_2 = factor + '_Down-regulated',
                )
            )

            return_table.append(example_metadata)

    return jsonify(return_table)

@app.route('/gallery/<species>', methods=['GET'])
def get_gallery(species):
    return render_template('gallery.html', species = species)

@app.route('/results/<path:task_id>/tabular/<label>')
def get_tabular_json(task_id, label):

    try:
        filepath = os.path.join(CONFIG.get('paths','root'), CONFIG.get('paths','upload'), task_id, label + '.lisa.tsv')
        tab_results = pd.read_csv(filepath, sep = '\t').set_index('Rank')
        return tab_results.to_json()
    except IOError:
        abort(404, description = 'resource not found')

@app.route('/results/<path:task_id>/metadata/<label>')
def get_metadata_json(task_id, label):
    try:
        filepath = os.path.join(CONFIG.get('paths','root'), CONFIG.get('paths','upload'), task_id, label + '.metadata.json')
        with open(filepath, 'r') as f:
            metadata = f.read()
        return metadata
    except IOError:
        abort(404, description = 'resource not found')

@app.route('/results/<path:task_id>/summary/<label>')
def get_summary_table(task_id, label):

    try:

        filepath = os.path.join(CONFIG.get('paths','root'), CONFIG.get('paths','upload'), task_id, label + '.lisa.tsv')
        tab_results = pd.read_csv(filepath, sep = '\t')

        top_factors = tab_results.head(100).drop_duplicates(subset = ['factor'], keep = 'first')\
            [['factor','summary_p_value']]

        top_factors['rank'] = top_factors.summary_p_value.rank()

        top_factors['summary_p_value'] = list(map(lambda x : "{:.2e}".format(x), top_factors.summary_p_value.values))

        factor_counts = tab_results.head(100).factor.value_counts()
        total_counts = tab_results.factor.value_counts()

        top_factors['top 100 appearances'] = [factor_counts[factor] for factor in top_factors.factor.values]
        top_factors['num samples'] = [total_counts[factor] for factor in top_factors.factor.values]

        return dataframe_to_json(top_factors)

    except IOError:
        abort(404, description = 'resource not found')


@app.route('/results/<path:task_id>/compare/<label_1>,<label_2>')
def compute_joined_dataframe(task_id, label_1, label_2):

    try:

        r1 = pd.read_csv(os.path.join(CONFIG.get('paths','root'), CONFIG.get('paths','upload'), task_id, label_1 + '.lisa.tsv'), sep = '\t')
        r2 = pd.read_csv(os.path.join(CONFIG.get('paths','root'), CONFIG.get('paths','upload'), task_id, label_2 + '.lisa.tsv'), sep = '\t')

        joined_data = r1.set_index('sample_id')[['factor', 'summary_p_value']].join(
            r2.set_index('sample_id')['summary_p_value'], lsuffix = '_1', rsuffix = '_2'
        )

        joined_data['-log10 ' + label_1] = -np.log10(joined_data.summary_p_value_1)
        joined_data['-log10 ' + label_2] = -np.log10(joined_data.summary_p_value_2)

        joined_data['list1_significant'] = joined_data.summary_p_value_1 < 0.0001
        joined_data['list2_significant'] = joined_data.summary_p_value_2 < 0.0001

        color_map = {(False,False) : "Neither", (True,False) : label_1, (False,True) : label_2, (True,True) : "Both"}

        joined_data['significance'] = [
            color_map[x] for x in zip(joined_data.list1_significant.values, joined_data.list2_significant.values)
        ]
        
        return dataframe_to_json(joined_data[['factor','-log10 ' + label_1, '-log10 ' + label_2, 'significance']].reset_index())  
    
    except IOError:
        abort(404, description = 'resource not found')


@app.route('/results/<path:task_id>/get/<path:filename>', methods = ['GET'])
def get_file(task_id, filename):
    return send_from_directory(os.path.join(CONFIG.get('paths','root'), CONFIG.get('paths','upload'), task_id), filename = filename)

# add new static folder
@app.route('/results/<path:task_id>/download', methods = ['GET'])
def download_results(task_id):
    return send_from_directory(os.path.join(CONFIG.get('paths','root'), CONFIG.get('paths','download')), filename = task_id + '.zip')

Bootstrap(app)