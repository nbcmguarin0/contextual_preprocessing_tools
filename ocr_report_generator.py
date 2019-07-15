import os
import io
import re
import pandas as pd
import math
import plotly.plotly as py
import plotly.graph_objs as go
import plotly.tools as tls
from datetime import datetime
import traceback
from bs4 import BeautifulSoup
from bs4.element import Comment
from collections import Counter

verbose = False

def readData(file_path, html=True):
    with io.open(file_path, encoding="utf-8") as file:
        if html:
            data = BeautifulSoup(file, "html.parser")
        else:
            data = file.read()
    return data
# end

def writeData(file_path, data, html=True):
    with open(file_path, "a") as file:
        file.write(data)
# end

def format_agg_report_html(tableData, cer, iframe_graphs, stats):
    # define html elements
    iframe_cer_by_doc, iframe_box_plot = iframe_graphs
    html_open_tag = "<html>"
    html_header = "<head><meta http-equiv='Content-Type' content='text/html; charset=UTF-8'>"
    html_open_body_tag = "<body>"
    cer_html = "<h4> Character Error Rate (aggregated across all documents): {} </h4>".format(cer)
    mean_html = "<h4> Mean Character Error Rate (across all documents): {} </h4>".format(stats["pop_mean"])
    msd_html = "<h4> Variance of Aggregated Character Error Rate Distribution: {} </h4>".format(stats["pop_msd"])
    std_html = "<h4> Standard Deviation of Aggregated Character Error Rate Distribution: {} </h4>".format(stats["pop_std"])
    html_close_body_tag = "</body>"
    html_close_tag = "</html>"
    cer_explaination = "<h3> What is Character/Word Error Rate? </h3><p>The general difficulty of measuring performance lies in the fact that the recognized character sequence can have a different length from the reference character sequence (supposedly the correct one). The WER/CER is derived from the Levenshtein distance, CER working at the character level and WER working at the word level. The WER/CER is a valuable tool for comparing different systems as well as for evaluating improvements within one system. This kind of measurement, however, provides no details on the nature of translation errors and further work is therefore required to identify the main source(s) of error and to focus any research effort.</p>"
    cer_formula = "<img src='https://wikimedia.org/api/rest_v1/media/math/render/svg/7db6226f0c365982b94f221d68530bf8a6a50611' class='mwe-math-fallback-image-inline' aria-hidden='true' style='vertical-align: -2.171ex; width:34.607ex; height:5.676ex;' alt='{\displaystyle {\mathit {WER}}={\frac {S+D+I}{N}}={\frac {S+D+I}{S+D+C}}}'> <p>where</p> <ul><li><i>S</i> is the number of substitutions,</li><li><i>D</i> is the number of deletions,</li><li><i>I</i> is the number of insertions,</li><li><i>C</i> is the number of the corrects,</li><li><i>N</i> is the number of words in the reference (N=S+D+C)</li></ul>"
    # bind html elements
    body_html = "{} <h2> Metrics </h2> {} {} {} {} {} {} <h2> Graphs </h2> <div> {} </div> <div> {} </div> <div> {} </div> <h2> Tables </h2> <center>{}</center>".format(html_open_body_tag, cer_explaination, cer_formula, cer_html, mean_html, msd_html, std_html, iframe_cer_by_doc, iframe_box_plot, tableData, html_close_body_tag)
    html_report_agg = "{} {} {} {}".format(html_open_tag, html_header, body_html, html_close_tag)
    return html_report_agg
# end

def formatData(data, title, col_names, typeOfData):
    formattedData = "<table border='1'><caption><h2>{}</caption></h2><tr>".format(title)
    for col_name in col_names:
        formattedData += "<td>{}</td>".format(col_name)
    formattedData +="</tr>"
    if typeOfData==0:
        for k, v in data.items():
            formattedData += "<tr><td>{}</td><td>{}</td><td>{}</td><td>{}</td><td>{}</td></tr>".format(k[0], k[1], v[0], v[1], v[2])
    else:
        for index, row in data.iterrows():
            formattedData += "<tr>"
            for elm in row:
                formattedData += "<td>{}</td>".format(elm)
            formattedData += "</tr>"
    return formattedData
# end

def tag_visible(element):
    if element.parent.name in ['style', 'script', 'head', 'title', 'meta', '[document]']:
        return False
    if isinstance(element, Comment):
        return False
    return True
# end

def text_from_html(body, joinchar=" "):
    soup = BeautifulSoup(body, 'html.parser')
    texts = soup.findAll(text=True)
    visible_texts = filter(tag_visible, texts)  
    return joinchar.join(t.strip() for t in visible_texts)
# end

def get_num_instances_confusedSpots(diff_spot_table_data, confusedSpots):
    total_elms_count = {}
    for elm in confusedSpots:
        if elm == ".":
            pattern = "["+elm+"]"
        else:
            pattern = elm
        try:
            total_elms_count[elm]=len(re.findall(pattern.replace(")", "\)").replace("(", "\("),
                                                          diff_spot_table_data.replace(")", "\)").replace("(", "\(")))
        except Exception as e:
            if verbose:
                traceback.print_exc()
            continue
    return total_elms_count
# end

def build_analytics_for_report(confusedSpots_zipped,  total_elms_count):
    typeOfGuess_total = {}
    for k in confusedSpots_zipped:
        try:
            if total_elms_count[k[0]]==0:
                typeOfGuess_total[k] = (confusedSpots_zipped[k], total_elms_count[k[0]], "undefined")
            else:
                typeOfGuess_total[k] = (confusedSpots_zipped[k], total_elms_count[k[0]], confusedSpots_zipped[k]/total_elms_count[k[0]])
        except KeyError as e:
            if verbose:
                traceback.print_exc()
            continue
    return typeOfGuess_total
# end

def format_for_dataframe_grnd_to_ocr(typeOfGuess_total):
    master_df_grnd_to_ocr = {}
    master_df_grnd_to_ocr["Ground_Truth"] = [k[0] for k in typeOfGuess_total.keys()]
    master_df_grnd_to_ocr["OCR_Output"] = [k[1] for k in typeOfGuess_total.keys()]
    master_df_grnd_to_ocr["ground_truth-ocr_output"] = ["{}-{}".format(k[0], k[1]) for k in typeOfGuess_total.keys()]
    master_df_grnd_to_ocr["total_combo"] = [v[0] for v in typeOfGuess_total.values()]
    master_df_grnd_to_ocr["total_occurances"] = [v[1] for v in typeOfGuess_total.values()]
    #master_df_grnd_to_ocr["guess_to_total"] = [v[2] for v in typeOfGuess_total.values()]
    master_df_grnd_to_ocr_df = pd.DataFrame(master_df_grnd_to_ocr)
    master_df_grnd_to_ocr_df[['total_combo', 'total_occurances']] = master_df_grnd_to_ocr_df[['total_combo', 'total_occurances']].astype(float)
    return master_df_grnd_to_ocr_df
# end

def format_for_dataframe(typeOfGuess_total):
    master_df_grnd_to_ocr = {}
    master_df_grnd_to_ocr["Character"] = [k[0] for k in typeOfGuess_total]
    master_df_grnd_to_ocr["HexCode"] = [k[1] for k in typeOfGuess_total]
    master_df_grnd_to_ocr["Total"] = [v[2] for v in typeOfGuess_total]
    master_df_grnd_to_ocr["Insertions"] = [v[3] for v in typeOfGuess_total]
    master_df_grnd_to_ocr["Substitutions"] = [v[4] for v in typeOfGuess_total]
    master_df_grnd_to_ocr["Deletions"] = [v[5] for v in typeOfGuess_total]
    #master_df_grnd_to_ocr["Error Rate"] = [v[6] for v in typeOfGuess_total]
    master_df_grnd_to_ocr_df = pd.DataFrame(master_df_grnd_to_ocr)
    master_df_grnd_to_ocr_df[["Total", "Insertions", "Substitutions", "Deletions"]] = master_df_grnd_to_ocr_df[["Total", "Insertions", "Substitutions", "Deletions"]].astype(float)
    return master_df_grnd_to_ocr_df
# end

def add_report_table(html_report_file_path):

    report_soup = readData(html_report_file_path) # read all html in file
    tables = report_soup.find('body').find_all('table', recursive=False) # all tables in html file as a list

    cmp_table_w_header = tables[0] # comparison table, first table in html
    cmp_table_wout_header = cmp_table_w_header.find_all('tr')[1] # just html text truth and test
    table_data_grnd_true = cmp_table_wout_header.find_all('td')[0] # table data ground truth text
    table_data_test = cmp_table_wout_header.find_all('td')[1] # table data test text

    # extract all text found in both truth and test tables 
    confusedSpots_grnd_true = [x.find('font').contents[0] for x in table_data_grnd_true.find_all('span')]
    confusedSpots_test = [x.find('font').contents[0] for x in table_data_test.find_all('span')]

    # zip grnd truth and test diffs
    confusedSpots_zipped=Counter([i for i in list(zip(confusedSpots_grnd_true, confusedSpots_test))])
    confusedSpots_grnd_true_str_html = str(table_data_grnd_true)
    confusedSpots_grnd_true_str_text = text_from_html(confusedSpots_grnd_true_str_html)

    total_elms_count = get_num_instances_confusedSpots(confusedSpots_grnd_true_str_text, confusedSpots_grnd_true)
    confused_elms_count = Counter(confusedSpots_grnd_true)
    typeOfGuess_total = build_analytics_for_report(confusedSpots_zipped, total_elms_count)

    reportTableInfo=formatData(data=typeOfGuess_total, title="Instances of OCR Failure: Ground Truth vs OCR Output", col_names=["Ground_Truth", "OCR_Output", "total_combo", "total_occurances", "guess_to_total"], typeOfData=0)
    writeData(file_path=os.path.join(os.getcwd(), html_report_file_path), data=reportTableInfo)
    master_df_grnd_to_ocr = format_for_dataframe_grnd_to_ocr(typeOfGuess_total)

    bs = BeautifulSoup(str(tables[1]), "html.parser")
    tds = [row.findAll('td') for row in bs.findAll('tr')]
    row_data = [(td[0].string,
                td[1].string,
                td[2].string,
                td[3].string,
                td[4].string,
                td[5].string,
                td[6].string,) for td in tds]
    rows_df = format_for_dataframe(typeOfGuess_total=row_data[1:])
    return master_df_grnd_to_ocr, rows_df 
# end

def calculate_stats(x):
    stats = {}
    stats["pop_mean"]=sum(x)/len(x) 
    diff_srq = lambda x: (x-stats["pop_mean"])**2
    stats["pop_msd"] = (1/len(x))*(sum(list(map(diff_srq, x)))) # variance using mean square difference
    stats["pop_std"] = math.sqrt(stats["pop_msd"])
    return stats
# end

def create_reports(output_dir_content, full_path_output_dir, tool, plotly_uname, plotly_api_key):
   grnd_to_ocr = []
   err_rate_per_char = []
   err_rate_per_doc = {}
   for outputfile in output_dir_content:
       # add report table to output file
       master_df_grnd_to_ocr, err_rate_per_char_df = add_report_table(outputfile)
       err_rate_per_doc[outputfile.split("/")[-1]] = (err_rate_per_char_df["Substitutions"].sum()
                                                     + err_rate_per_char_df["Insertions"].sum()
                                                     + err_rate_per_char_df["Deletions"].sum())/err_rate_per_char_df["Total"].sum()
                                                                              
       # bundle stats from report added to html in dataframe in list
       grnd_to_ocr.append(master_df_grnd_to_ocr)
       err_rate_per_char.append(err_rate_per_char_df)

   currenttime = datetime.now().strftime("%Y%m%d%H%M%S")

   err_rate_per_doc_df = pd.DataFrame(list(err_rate_per_doc.items()),
                                      columns=["filename", "CER"])

   # register plotly credentials to put plot on remote server 
   tls.set_credentials_file(plotly_uname, plotly_api_key)

   # calculate basic stats on CER 
   stats = calculate_stats(err_rate_per_doc_df["CER"].tolist())

   # cer by document plotly RAW BAR GRAPH OF VALUES
   data = [go.Bar(
                x=err_rate_per_doc_df["filename"].tolist(),
                y=err_rate_per_doc_df["CER"].tolist()
          )]
   layout = go.Layout(
                      title="CER by document",
                      xaxis=dict(title="Documents"),
                      yaxis=dict(title="Character Error Rate"),
                     )
   fig = go.Figure(data=data, layout=layout)
   httpplot = py.plot(fig, filename="Basic_Bar_CER_AcrossDocs_{}_{}".format(tool, currenttime))
   iframe_cer_by_doc = tls.get_embed(httpplot)

   # PROBABILITY DENSITY FUNCTIONS
   y_outliers_removed_2std = list(filter(lambda x: x<(stats["pop_mean"]+2*stats["pop_std"]) and x>(stats["pop_mean"]-2*stats["pop_std"]), list(map(float, err_rate_per_doc_df["CER"].tolist()))))
   y_outliers_removed_1std = list(filter(lambda x: x<(stats["pop_mean"]+1*stats["pop_std"]) and x>(stats["pop_mean"]-1*stats["pop_std"]), list(map(float, err_rate_per_doc_df["CER"].tolist()))))
   y = list(map(float, err_rate_per_doc_df["CER"].tolist()))
   hist_data = [y, y_outliers_removed_1std, y_outliers_removed_2std]
   group_labels = ["CERs_actual", "CERs_outliers_removed_1std", "CERs_outliers_removed_2std"]
   colors = ["#333F44", "#008080", "#FF33FF"]
   #fig = ff.create_distplot(hist_data, group_labels, show_hist=False, colors=colors)
   #fig["layout"].update(title="Comparison of CER Probability Density Functions", xaxis=dict(title="Character Error Rate"))
   #httpplot = py.plot(fig, filename="Curve and Rug_{}".format(tool))
   #iframe_cer_dist = tls.get_embed(httpplot)

   # BOX PLOTS
   trace0 = go.Box(
           y = y,
           boxpoints="all",
           name="CERs_actual",
           marker= dict(color="#333F44",),
           boxmean=True
           )
   trace1 = go.Box(
           y = y_outliers_removed_1std,
           boxpoints="all",
           name="CERs_outliers_removed_1std",
           marker= dict(color="#008080",),
           boxmean=True
           )
   trace2 = go.Box(
           y = y_outliers_removed_2std,
           boxpoints="all",
           name="CERs_outliers_removed_2std",
           marker= dict(color="#FF33FF",),
           boxmean=True
           )

   data=[trace0, trace1, trace2]
   layout = go.Layout(
                      title="Box Plot: CER Distribution Comparision",
                      yaxis=dict(title="Character Error Rates"),
                     )

   fig = go.Figure(data=data, layout=layout)
   httpplot = py.plot(fig, filename="Box_Plot_CER_Distribution_Comparision_{}_{}".format(tool, currenttime))
   iframe_box_plot = tls.get_embed(httpplot)

   # vertically stack dataframes from bundled list above
   grnd_to_ocr_df_agg = pd.concat(grnd_to_ocr[:],axis=0)
   err_rate_per_char_df_agg = pd.concat(err_rate_per_char[:],axis=0)

   # combine rows that pertain to same values in vertically stacked dataframes
   grnd_to_ocr_df_agg = grnd_to_ocr_df_agg.groupby(["Ground_Truth","OCR_Output", "ground_truth-ocr_output"], as_index=False)["total_combo", "total_occurances"].sum()
   err_rate_per_char_df_agg = err_rate_per_char_df_agg.groupby(["Character","HexCode"], as_index=False)["Substitutions","Deletions","Insertions","Total"].sum() 

   # drop unnecessary columns in aggregated dataframes
   err_rate_per_char_df_agg = err_rate_per_char_df_agg.drop(err_rate_per_char_df_agg[err_rate_per_char_df_agg.Total==0].index)
   grnd_to_ocr_df_agg = grnd_to_ocr_df_agg.drop(grnd_to_ocr_df_agg[grnd_to_ocr_df_agg.total_occurances==0].index)
   grnd_to_ocr_df_agg = grnd_to_ocr_df_agg.drop("ground_truth-ocr_output",axis=1)

   # perform character rate calculation
   err_rate_per_char_df_agg["Error_Rate"] = err_rate_per_char_df_agg.apply(lambda row: (sum([row["Substitutions"],
                                                                                             row["Insertions"],
                                                                                             row["Deletions"]])
                                                                                       /row["Total"]) 
                                                                                       if row["Total"] > 0
                                                                                       else "Infinity",
                                                                                       axis=1)

   grnd_to_ocr_df_agg["Total_Combo_by_total_occurances"] = grnd_to_ocr_df_agg.apply(lambda row: row["total_combo"] / row["total_occurances"] if row["total_occurances"] > 0 else "Undefined", axis=1)

   agg_char_err_rate = sum([err_rate_per_char_df_agg["Substitutions"].sum(),
                        err_rate_per_char_df_agg["Insertions"].sum(),
                        err_rate_per_char_df_agg["Deletions"].sum()]) / err_rate_per_char_df_agg["Total"].sum() 
   #err_rate_per_char_df_agg.to_csv("after_err_rate_per_char_df_agg.csv", sep=",")
   grnd_to_ocr_html_table = formatData(data=grnd_to_ocr_df_agg,
                                       title="Instances of OCR Failure: Ground Truth vs OCR Output",
                                       col_names=grnd_to_ocr_df_agg.columns,
                                       typeOfData=1)
   err_rate_per_char_html_table = formatData(data=err_rate_per_char_df_agg,
                                             title="Error Rate Per Character",
                                             col_names=err_rate_per_char_df_agg.columns,
                                             typeOfData=1)
   #html_report_agg = format_agg_report_html(tableData=err_rate_per_char_html_table+"<br>"+"<br>"+grnd_to_ocr_html_table, cer=agg_char_err_rate, iframe_graphs=[iframe_cer_by_doc, iframe_cer_dist, iframe_box_plot], stats=stats)
   html_report_agg = format_agg_report_html(tableData=err_rate_per_char_html_table+"<br>"+"<br>"+grnd_to_ocr_html_table, cer=agg_char_err_rate, iframe_graphs=[iframe_cer_by_doc, iframe_box_plot], stats=stats)
   writeData(file_path=os.path.join(full_path_output_dir, "{}_aggregated_report.html".format(tool)), data=html_report_agg)
# end
