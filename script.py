import datetime
import pygal
from pygal.style import RedBlueStyle
import dominate
from dominate.tags import *
import pdfkit

def generateReport(reportDate, domain, goalTop, chartData, positionsData, absolutePath):
    ya, g, dates = [], [], []
    for data in chartData:
        position = round(data['position'], 0)
        if data['name_se'] == 'Яндекс':
            date = datetime.datetime.strptime(data['report_date'], "%Y-%m-%d")
            dates.append(date.strftime("%d.%m.%y"))
            ya.append(position)
        if data['name_se'] == 'Google':
            g.append(position)

    #generate positions chart
    customStyle = RedBlueStyle
    customStyle.background = '#ffffff'
    customStyle.colors = ('#FF0000', '#4087F1')
    customStyle.guide_stroke_dasharray = '4,4'
    customStyle.major_guide_stroke_dasharray = '4,4'
    customStyle.foreground = '#666666'
    customStyle.foreground_strong = '#666666'
    customStyle.foreground_subtle = '#999999'
    customStyle.font_family = 'Arial, Helvetica, sans-serif'
    customStyle.label_font_size = 24
    customStyle.major_label_font_size = 24
    customStyle.value_font_size = 24
    customStyle.opacity = 1
    line_chart = pygal.Line(
        show_legend=False,
        style=customStyle,
        width=2000, height=1100,
        margin_top = 0,
        margin_bottom = 40,
        margin_left = 0,
        margin_right = 30,
        human_readable=True,
        x_label_rotation=-25,
        range=(0, 101),
        print_values=True,
        show_x_guides=True,
        interpolate='cubic',
        stroke_style = {'width': 5, 'dasharray': '1', 'linecap': 'round', 'linejoin': 'round'},
        dots_size=7,
        inverse_y_axis=True,
        y_labels = [
            {'label': '< 100', 'value': 101},
            {'label': '90', 'value': 90},
            {'label': '80', 'value': 80},
            {'label': '70', 'value': 70},
            {'label': '60', 'value': 60},
            {'label': '50', 'value': 50},
            {'label': '40', 'value': 40},
            {'label': '30', 'value': 30},
            {'label': '20', 'value': 20},
            {'label': '10', 'value': 10},
            {'label': '1', 'value': 1}])
    line_chart.add('Яндекс', ya)
    line_chart.add('Google', g)
    line_chart.x_labels = dates
    line_chart.render_to_png('positions.png')
    print('Chart generated')
    
    #arrange data for positions table
    positionsForTable, uniquePositionDates, uniqueQueries = {}, [], []
    for item in positionsData:
        date = item['pretty_report_date']
        query = item['query']
        queryAlreadyAdded = False
        dateAlreadyAdded = False
        for addedDate in uniquePositionDates:
            if addedDate == date:
                dateAlreadyAdded = True
                break
        if not dateAlreadyAdded:
            uniquePositionDates.append(date)
        for addedQuery in uniqueQueries:
            if addedQuery == query:
                queryAlreadyAdded = True
                break
        if not queryAlreadyAdded:
            uniqueQueries.append(query)
    uniqueQueriesSorted = sorted(uniqueQueries)
    uniquePositionDatesSorted = sorted(uniquePositionDates)
    for query in uniqueQueries:
        queryStat = {}
        for date in uniquePositionDates:
            queryStat[date] = {}
            for statItem in positionsData:
                if statItem['query'] == query and statItem['pretty_report_date'] == date:
                    if statItem['name_se'] == 'Google':
                        queryStat[date]['g'] = statItem['position']
                    if statItem['name_se'] == 'Яндекс':
                        queryStat[date]['ya'] = statItem['position']
        positionsForTable[query] = queryStat
    avgPositions = {}
    for date in uniquePositionDatesSorted:
        avgPositions[date] = {}
        avgPositions[date]['ya'] = {}
        avgPositions[date]['ya']['sum'] = 0
        avgPositions[date]['ya']['count'] = 0
        avgPositions[date]['ya']['avg'] = 0
        avgPositions[date]['g'] = {}
        avgPositions[date]['g']['sum'] = 0
        avgPositions[date]['g']['count'] = 0
        avgPositions[date]['g']['avg'] = 0
    for key in positionsForTable:
        for date in uniquePositionDatesSorted:
            posYa = positionsForTable[key][date].get('ya', 0)
            avgPositions[date]['ya']['sum'] += posYa
            avgPositions[date]['ya']['count'] += 1 if posYa > 0 else 0
            posG = positionsForTable[key][date].get('g', 0)
            avgPositions[date]['g']['sum'] += posG
            avgPositions[date]['g']['count'] += 1 if posG > 0 else 0
    #generate html
    doc = dominate.document(title='Report')
    with doc.body:
        with div(_class = "title-logo"):
            img(src = absolutePath + "unkle_logo.png")
        with h1('Отчет по позициям ', _class="main-title"):
            br()
            a(domain, href="http://" + domain)
            br()
            span(reportDate)
        with div(_class = "page-break position-relative"):
            img(src = absolutePath + "unkle_guy.png", _class = "pin-bottom-left")
            img(src = absolutePath + "unkle_checkers.png", _class = "pin-bottom-right")
        h2('Динамика средних позиций')
        with div(_class='chart-legend'):
            span(' ', _class='chart-series-symbol yandex')
            span(' Яндекс')
        with div(_class='chart-legend margin-left'):
            span(' ', _class='chart-series-symbol google')
            span(' Google')
        img(_class = "chart", src = absolutePath + 'positions.png')
        div(_class = "page-break")
        h2('Позиции по запросам')
        i = 1
        yaSum, gSum = 0, 0
        with div(_class='table-wrapper'):
            with table(align="center"):
                with tbody(_class='thead'):
                    with tr():
                        th('№', rowspan=2)
                        th('Запрос', rowspan=2)
                        for date in uniquePositionDatesSorted:
                            th(date, colspan=2, _class='text-center')
                    with tr():
                        for date in uniquePositionDatesSorted:
                            th('Яндекс')
                            th('Google')
                with tbody():
                    for query in uniqueQueriesSorted:
                        queryStat = positionsForTable.get(query, {})
                        with tr():
                            td(i)
                            td(query, _class='text-left')
                            for date in uniquePositionDatesSorted:
                                statForDate = queryStat.get(date, {})
                                ya = statForDate.get('ya', 1000)
                                g = statForDate.get('g', 1000)
                                classYa = 'color-green' if ya <= goalTop else ''
                                classG = 'color-green' if g <= goalTop else ''
                                with td(_class = classYa):
                                    img(src = absolutePath + 'ya_icon.png', _class="yandex-icon")
                                    if ya < 1000:
                                        span(ya)
                                    else:
                                        span('–')
                                with td(_class = classG):
                                    img(src = absolutePath + 'g_icon.png', _class="google-icon")
                                    if g < 1000:
                                        span(g)
                                    else:
                                        span('–')
                        i += 1
                if i > 0:
                    with tbody(_class='tfoot'):
                        with tr():
                            td('Средняя позиция', colspan = 2)
                            for date in uniquePositionDatesSorted:
                                yaSum = avgPositions.get(date, {}).get('ya', {}).get('sum', 0)
                                yaCount = avgPositions.get(date, {}).get('ya', {}).get('count', 0)
                                yaAvg = yaSum / yaCount if yaCount > 0 else 1000
                                gSum = avgPositions.get(date, {}).get('g', {}).get('sum', 0)
                                gCount = avgPositions.get(date, {}).get('g', {}).get('count', 0)
                                gAvg = gSum / gCount if gCount > 0 else 1000
                                classYaAvg = 'color-green' if yaAvg <= goalTop else ''
                                classGAvg = 'color-green' if gAvg <= goalTop else ''
                                with td( _class = classYaAvg):
                                    img(src = absolutePath + 'ya_icon.png', _class="yandex-icon")
                                    if yaAvg < 1000:
                                        span('{:.0f}'.format(yaAvg))
                                    else:
                                        span('–')
                                with td(_class = classGAvg):
                                    img(src = absolutePath + 'g_icon.png', _class="google-icon")
                                    if gAvg < 1000:
                                        span('{:.0f}'.format(gAvg))
                                    else:
                                        span('–')
    #print(doc.render())
    print('HTML generated')

    #generate pdf from html
    options = {
        'page-size': 'A4',
        'margin-top': '2cm',
        'margin-right': '2cm',
        'margin-bottom': '2cm',
        'margin-left': '2cm',
        'encoding': "UTF-8",
        'no-outline': None,
        'orientation': 'Landscape'
    }
    pdfkit.from_string(doc.render(), 'out.pdf', options = options, css = absolutePath + 'styles.css')
    print('PDF generated')


#import data from json
import json
positionsJson = open("position_table.json").read()
positionsData = json.loads(positionsJson)
chartDataJson = open("graph_data.json").read()
chartData = json.loads(chartDataJson)

#generate report
generateReport('02.10.17', 'citadelpark.ru', 10, chartData, positionsData, '/Users/alexandrdemin/Desktop/unkle/')