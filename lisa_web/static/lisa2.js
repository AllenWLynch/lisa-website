function tabulate(cl, data, columns) {
  var table = d3.select("." + cl).append("table")
        .attr("class", "hover row-border table-bordered tab" + cl),
      thead = table.append("thead"),
      tbody = table.append("tbody").attr("class", "tbody");

  // append the header row
  thead.append("tr")
  .selectAll("th")
  .data(columns)
  .enter()
  .append("th")
      .text(function(column) { return column; });

  // create a row for each object in the data
  var rows = tbody.selectAll("tr")
    .data(data)
    .enter()
    .append("tr");

  // create a cell in each row for each column
  var cells = rows.selectAll("td")
    .data(function(row) {
        return columns.map(function(column) {
            return {column: column, value: row[column]};
        });
    })
    .enter()
    .append("td")
        .text(function(d) { return d.value; });

  $('.tab' + cl).ready(function() {
    $('.tab'+ cl).DataTable({
      "order": [],
      retrieve: true,
      // destroy: true,
      paging: true,
      dom: 'Bfrtip',
      buttons: [
          'csv', 'excel', 'pdf'
      ]
    });
  });

  return table;
  
}

function fetch(row, test_type) {
  if (test_type == 'motif') {
    $('td').click(function(e) {
      $(".annotation").html("");
      $(".annotation").append("<div><img class='img-fluid' style='vertical-align:middle' height='240' width='320' src='http://lisa.cistrome.org/static/" + $(this).attr('data_id') + ".pwm.jpg'></div>");
      $(".annotation").show(500);
    })
    return;
  }

  if (!row) {
    selector = "td";
  } else {
    selector = "tr";
  }
        $(selector).click(function(e) {
          var bookId = $(this).attr('data_id'); // this works
          $.getJSON('http://dc2.cistrome.org/api/inspector?id='+bookId, function(d) {

          $("body, html").animate({
            scrollTop: $('.annotation').offset().top - $('.dataTable').offset().top
          }, 600);

            $(".annotation").html("");
            conserv="http://dc2.cistrome.org/api/conserv?id="+bookId;
            color = {true: "green", false: "red", "NA": "gray"};

            if (d.treats[0].species__name == "Homo sapiens") {
               browser_sp = "hg38"
            } else {
               browser_sp = "mm10"
            }

            if (d.treats[0].unique_id.startsWith('GSM')) {
                link = 'http://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=' + d.treats[0].unique_id;
            } else {
                // https://www.encodeproject.org/experiments/ENCSR264RJX/
                link = 'https://www.encodeproject.org/experiments/' + d.treats[0].unique_id.split('_')[0];
            }

            modelc = $('<div class="card"><div class="card-header"><div class="card-title"><h3><b>Inspector</b></h3></div></div><div class="card-body"><div class="row"><div class="col-sm-9"><div class="row inspector_attrib_row"><div class="col"><b>Title:</b></div><div class="col">' + d.treats[0].name + '</div></div>' + 
                       '<div class="row inspector_attrib_row"><div class="col"><b>GEO or ENCODE:</b></div><div class="col"><p class="tight-line">' + '<a href="' + link + '">' + d.treats[0].unique_id + '</a></div></div>' + 
                       '<div class="row inspector_attrib_row"><div class="col"><b>Species:</b></div><div class="col"><p>' + d.treats[0].species__name + '</p></div></div>' + 
                       '<div class="row inspector_attrib_row"><div class="col"><b>Citation:</b></div><div class="col"><p>' + d.treats[0].paper__reference + '</p>' +'PMID:' + '<a href="https://www.ncbi.nlm.nih.gov/pubmed/?term=' + d.treats[0].paper__pmid + '">' + d.treats[0].paper__pmid + '</a></div></div>' + 
                       '<div class="row inspector_attrib_row"><div class="col"><b>Species:</b></div><div class="col"><p>' + d.treats[0].species__name + '</p></div></div>' + 
                       '<div class="row inspector_attrib_row"><div class="col"><b>Factor:</b></div><div class="col"><p>' + d.treats[0].factor__name + '</p></div></div>' +
                       '<div class="row inspector_attrib_row"><div class="col"><b>Biological Source:</b></div><div class="col"><p class="tight-line"><b>Cell Line:</b>' + d.treats[0].cell_line__name + '</p>' +  
                                        '<p class="tight-line"><b>Cell Type:</b>' + d.treats[0].cell_type__name + '</p>' + 
                                        '<p class="tight-line"><b>Tissue:</b>' + d.treats[0].tissue_type__name + '</p>' + 
                                        '<p class="tight-line"><b>Disease:</b>' + d.treats[0].disease_state__name + '</p></div></div></div>' + 
  '<div class="col-sm-3"><div class="row"><div class="col"><b>Quality Control</b></div></div>' + 
  '<div class="row"><div class="col">' + 
     '<div class="circle-col"><div class="circle ' + color[d.qc.judge.fastqc] + '"' + 'data-toggle="tooltip" data-html="true" data-placement="auto" data-original-title="<strong class=\'text-primary\'>Sequence Quality:</strong><br> Raw sequence median quality score and raw read GC contents"></div></div>' +
     '<div class="circle-col"><div class="circle ' + color[d.qc.judge.map] + '"' + 'data-toggle="tooltip" data-html="true" data-placement="auto" data-original-title="<strong class=\'text-primary\'>Mapping Quality:</strong><br> Uniquely mapped ratio"></div></div>' +
     '<div class="circle-col"><div class="circle ' + color[d.qc.judge.pbc] + '"' + 'data-toggle="tooltip" data-html="true" data-placement="auto" data-original-title="<strong class=\'text-primary\'>Library Complexity:</strong><br> PCR bottleneck coefficient (PBC)"></div></div>' +
     '<div class="circle-col"><div class="circle ' + color[d.qc.judge.peaks] + '"' + 'data-toggle="tooltip" data-html="true" data-placement="auto" data-original-title="<strong class=\'text-primary\'>ChIP enrichment:</strong><br> Sufficient number of peaks(above 500) with good enrichment(10 fold change)"></div></div>' +
     '<div class="circle-col"><div class="circle ' + color[d.qc.judge.frip] + '"' + 'data-toggle="tooltip" data-html="true" data-placement="auto" data-original-title="<strong class=\'text-primary\'>Signal to Noise Ratio:</strong><br> Fraction of reads in peaks (FRiP)"></div></div>' +
     '<div class="circle-col"><div class="circle ' + color[d.qc.judge.dhs] + '"' + 'data-toggle="tooltip" data-html="true" data-placement="auto" data-original-title="<strong class=\'text-primary\'>Regulatory Region:</strong><br> "DNase-seq union hypersensitive sites" (DHS) overlapped ratio in top 5000 peaks"></div></div>' +
  '</div></div>' + 
  '<div class="row"><div class="col"><b>Visualize</b></div></div>' + 
    //http://epigenomegateway.wustl.edu/browser/?genome=hg38&hub=http://dc2.cistrome.org/api/datahub/93&gftk=refGene,full
  '<div class="row"><div class="col"><div class="btn-group">' + '<a target="_blank" id="genomebrowser-bw" type="button" class="btn btn-default button-list" href="http://epigenomegateway.wustl.edu/browser/?genome='+browser_sp+'&hub=http://dc2.cistrome.org/api/datahub/'+d.id+'&gftk=refGene,full">WashU</a><a target="_blank" id="genomebrowser-bw" type="button" class="btn btn-default button-list" href="http://dc2.cistrome.org/api/hgtext/' + d.id + '/?db=' + browser_sp + '">UCSC</a></div></div></div>' + 
  '</div></div>');
  $(".annotation").append( modelc );
  modelc = $('<div class="card"><div class="card-header">Tool</div><div class="card-body"><table class="table">' +
                       '<thead><tr><th>QC</th><th>Value</th></tr></thead>' +
                       '<tbody><tr><td>Mappable Reads</td>' + '<td>' + d.qc.table.map_number[0] + '</td></tr>' + 
                       '<tr><td>Mappable ratio</td><td>' + d.qc.table.map[0] + '</td></tr>' +
                       '<tr><td>PBC</td><td>' + d.qc.table.pbc[0] + '</td></tr>' +
                       '<tr><td>Peak number</td><td>' + d.qc.table.peaks[0] + '</td></tr>' + 
                       '<tr><td>FRiP</td><td>' + d.qc.table.frip[0] + '</td></tr>' + 
                       '<tr><td>Peaks in promoter/exon/intron/intergenic</td><td>' + d.qc.table.meta + '</td><tr>' +
                       '<tr><td>DHS ratio</td><td>' + d.qc.table.dhs + '</td></tr>' +
                       '<tr><td>Conservation plot</td><td><img class="img-fluid" height="400" width="400" src="' + conserv + '">' + '</td></tr></tbody>' +
                       '</table></div></div>');
   $(".annotation").append( modelc );
            if (d.motif) {
              console.log(d.motif_url);
              m = 'http://dc2.cistrome.org/'+d.motif_url;
              modelc = $('<div class="row"><iframe height="800" width="100%" src="' + m + '"></div>');
              $(".annotation").append( modelc );
            }
            $(".annotation").show(500);
          });
        });
}

function update_relational_plot(joined_results, label_1, label_2) {

  var margin = {top: 15, right: 20, bottom: 50, left: 50},
    width = 1000 - margin.left - margin.right,
    height = 650 - margin.top - margin.bottom;

  var cmap = {Neither : "lightgrey", Both : "purple"};

  label_1_screen_name = label_1.replaceAll('_',' ')
  label_2_screen_name = label_2.replaceAll('_', ' ')

  cmap[label_1_screen_name] = "orange";
  cmap[label_2_screen_name] = "#0099CC";

/* 
 * value accessor - returns the value to encode for a given data object.
 * scale - maps value to a visual display encoding, such as a pixel position.
 * map function - maps from data value to display value
 * axis - sets up axis
 */ 

  // setup x 
  var xValue = function(d) { return d['-log10 ' + label_1];}, // data -> value
      xScale = d3.scaleLinear().range([0, width]), // value -> display
      xMap = function(d) { return xScale(xValue(d));}, // data -> display
      xAxis = d3.axisBottom(xScale);

  // setup y
  var yValue = function(d) { return d['-log10 ' + label_2];}, // data -> value
      yScale = d3.scaleLinear().range([height, 0]), // value -> display
      yMap = function(d) { return yScale(yValue(d));}, // data -> display
      yAxis = d3.axisLeft(yScale);

  // setup fill color
  var cValue = function(d) { return d.significance;},
      color = function(d) {return cmap[d.replaceAll('_', ' ')];};

  // add the graph canvas to the body of the webpage
  var svg = d3.select(".tf1_fig").append("svg")
      .attr("width", width + margin.left + margin.right)
      .attr("height", height + margin.top + margin.bottom)
      .append("g")
      .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

  // add the tooltip area to the webpage
  var tooltip = d3.select(".tf1_fig").append("div")
      .attr("class", "tooltip")
      .style("opacity", 0);

    // load data
  d3.json(joined_results, function(error, data) {
    if (error) throw error;

    // change string (from CSV) into number format
    data.forEach(function(d) {
      d['-log10 ' + label_1] = +d['-log10 ' + label_1];
      d['-log10 ' + label_2] = +d['-log10 ' + label_2];
    });

    // don't want dots overlapping axis, so add in buffer to data domain
    xScale.domain([d3.min(data, xValue)-1, d3.max(data, xValue)+1]);
    yScale.domain([d3.min(data, yValue)-1, d3.max(data, yValue)+1]);

    // Add the x Axis
    svg.append("g")
      .attr("transform", "translate(0," + height + ")")
      .call(d3.axisBottom(xScale));

    // text label for the x axis
    svg.append("text")             
      .attr("transform",
            "translate(" + (width/2) + " ," + 
                          (height + margin.top + 20) + ")")
      .style("text-anchor", "middle").style("font-size","13px")
      .text("-log10 " + label_1_screen_name);

    // Add the y Axis
    svg.append("g")
      .call(d3.axisLeft(yScale));

    // text label for the y axis
    svg.append("text")
      .attr("transform", "rotate(-90)")
      .attr("y", 0 - margin.left)
      .attr("x",0 - (height / 2))
      .attr("dy", "1em")
      .style("text-anchor", "middle").style("font-size", "13px")
      .text("-log10 " + label_2_screen_name);  

    // draw dots
    svg.selectAll(".dot")
        .data(data)
      .enter().append("circle")
        .attr("class", "dot")
        .attr("r", 3.5)
        .attr("cx", xMap)
        .attr("cy", yMap)
        .style("fill", function(d) { 
            return color(cValue(d)); 
        }).on("mouseover", function(d) {
          tooltip.transition()
            .duration(200)
            .style("opacity", .9);
          tooltip.html(d.factor)
            .style("left", (xMap(d) + 90) + "px")
            .style("top", (yMap(d) + 100) + "px");
          })
        .on("mouseout", function(d) {
          tooltip.transition()
            .duration(500)
            .style("opacity", 0);
          });

    // draw legend
    var legend = svg.selectAll(".legend")
        .data(["Neither", label_1_screen_name, label_2_screen_name, "Both"])
      .enter().append("g")
        .attr("class", "legend")
        .attr("transform", function(d, i) { return "translate(0," + i * 20 + ")"; });

    // draw legend colored rectangles
    legend.append("circle")
        .attr("cx", width)
        .attr("r", 5)
        .style("fill", function(d) {
          return color(d); 
      });

    // draw legend text
    legend.append("text")
        .attr("x", width - 24)
        .attr("dy", ".35em")
        .style("text-anchor", "end")
        .text(function(d) { 
          if (d=="Neither") {
            return 'Significant to Neither'
          } else {
            return 'to ' + d
          };
        })
        
  });
}


function update_progress(status_url, status_div, results_1, results_2, joined_results, label_1, label_2) {
  // send GET request to status URL
  $.getJSON(status_url, function(data) {
    $(document).ready(function() {
        $("body").tooltip({ selector: '[data-toggle=tooltip]' });
    });

    // update UI
    $(status_div.childNodes[0]).css("width", data['status']);
    $(status_div.childNodes[0]).text(data['status']+ " " + data['state']);

    if (data['state'] == 'DONE') {
      $('.progress').hide();
      $(".result").show(1500);
      $("h4").text("Compare Gene Sets")
      
      var columns = ['rank','factor','summary_p_value','top 100 appearances', 'num samples'];

      console.log(results_1)
      console.log(results_2)
      console.log(joined_results)

      update_relational_plot(joined_results, label_1, label_2)
      $('.leftpanel a[href="#tf1_fig"]').click(function(e){
        $('.active').removeClass("active");
        $(".annotation").hide();
        $(".annotation").html("");
        $("h4").text("Compare Gene Sets")
        $(this).tab('show');
      });

      d3.json(results_1, function(error, d) {
        if (error) throw error;

        tabulate('tf1', d, columns);
        // fetch(false);
        $('.dataTable').on('draw.dt', function() {
          //fetch(false);
        });
      });
      $('.leftpanel a[href="#tf1"]').click(function(e) {
        $('.active').removeClass("active");
        $(".annotation").html("");
        $("h4").text(label_1.replaceAll('_', ' ') + " Results")
        $(this).tab('show');
      });

      d3.json(results_2, function(error, d) {
        tabulate('tf2', d, columns);
        //fetch(false, 'motif');
        $('.dataTable').on('draw.dt', function() {
          //fetch(false, 'motif');
        });
      });
      $('.leftpanel a[href="#tf2"]').click(function(e){
        $('.active').removeClass("active");
        $(".annotation").hide();
        $(".annotation").html("");
        $("h4").text(label_2.replaceAll('_', ' ') + " Results")
        $(this).tab('show');
      });

    } else if (data['state'] == 'ERROR') {
      
      $('.progress').hide();
      $("h4").text(data['status']);
    } else if (data['state'] == 'TASK DNE') {
      window.location.href = "/404";
    } else {
      setTimeout(function() {
        update_progress(status_url, status_div, results_1, results_2, joined_results, label_1, label_2);
      }, 9000);  // extend to 9000ms for post-process the snakemake results to avoid dataTable issues
    }
  });
}

function start_lisa_task(id, results_1, results_2, joined_results, label_1, label_2, method) {
  // $(".result").hide();
  // add task status elements
  div = $('<div class="progress"><div class="progress-bar progress-bar-striped progress-bar-animated" role="progressbar" role="progressbar" aria-valuenow="0" aria-valuemin="0" aria-valuemax="100"></div></div><hr>');

  $('.lisa_progress').append(div);

  $.ajax({
    type: 'POST',
    url: id,
    success: function(data, status, request) {
      update_progress(id, div[0], results_1, results_2, joined_results, label_1, label_2, method);
    },
    error: function() {
      alert('Unexpected error');
    }
  });
}