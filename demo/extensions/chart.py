import pygal
import re

import roundup.hyperdb as hyperdb

from roundup.anypy.strings import bs2b
from roundup.cgi import templating
from roundup.cgi.actions import Action

from collections import defaultdict

from pygal.style import Style


import logging
logger = logging.getLogger('extension')

log = []


class ChartingAction(Action):

    jsURL = None
    # jsURL = "https://kozea.github.io/pygal.js/2.0.x/pygal-tooltips.js"
    # uncomment and set to url for local copy of pygal-tooltips.js
    jsURL = "https://rouilj.dynamic-dns.net/sysadmin/@@file/jslibraries/pygal-tooltips.js"

    # set output image type. svg and data: are interactive
    output_type = "image/svg+xml"  # @image_type: image/svg+xml, image/png, data:

    # image is to be embedded in a rendered html page rather than stand alone.
    embedded = False  # @embedded: 0, 1

    def get_data_from_query(self, db, classname=None, filterspec=None,
                            group=None, search_text=None, **other):
        """parse and summarize the query submitted into a data table.
           also look for @image_type= and set output_type appropriately
           and @embedded (boolean) and set it properly. embedded not yet used.
        """
        cl = db.getclass(classname)
        log.append('cl=%s' % cl)

        # full-text search
        if search_text:
            matches = db.indexer.search(re.findall(r'\b\w{2,25}\b',
                                                   search_text), cl)
        else:
            matches = None
        log.append('matches=%s' % matches)

        # if group is a list, extract first property ...
        # group may also be a single tuple
        # FIXME support multiple property group
        property = None
        if isinstance(group, type([])):
            property = group[0][1]
        elif isinstance(group, type(())):
            property = group[1]

        log.append('property=%s' % property)

        try:
            prop_type = cl.getprops()[property]
            log.append('prop_type=%s' % prop_type)
        except KeyError:
            raise ValueError(
                'Charts can only be created on '
                'linked group properties! %s is not '
                'a valid property\n' % property)

        if not isinstance(prop_type, hyperdb.Link) \
           and not isinstance(prop_type, hyperdb.Multilink):
            raise ValueError(
                'Charts can only be created on '
                'linked group properties! %s is not '
                'a linked property\n' % property)
            return

        klass = db.getclass(prop_type.classname)
        log.append('klass=%s' % klass)

        # build a property dict, eg: { 'new':1, 'assigned':2 }
        # in
        # case of status
        props = {}

        if not filterspec:
            filterspec = {}

        issues = cl.filter(matches, filterspec, sort=[('+', 'id')],
                           group=group)

        log.append('issues=%s' % issues)
        for nodeid in issues:
            if not self.hasPermission('View', itemid=nodeid,
                                      classname=cl.classname):
                continue
            prop_ids = cl.get(nodeid, property)
            if prop_ids:
                if not isinstance(prop_ids, type([])):
                    prop_ids = [prop_ids]
                for id in prop_ids:
                    prop = klass.get(id, klass.labelprop())
                    key = prop.replace('/', '-')
                    if key in props:
                        props[key] += 1
                    else:
                        props[key] = 1
            else:
                prop = 'Unassigned'
                if prop not in props:
                    props[prop] = 0
                key = prop.replace('/', '-')
                if key in props:
                    props[key] += 1
                else:
                    props[key] = 1
        log.append('props=%s' % props)
        chart = [(k, v) for k, v in props.items()]

        if '@image_type' in self.form:
            self.output_type = self.form['@image_type'].value

        if '@embedded' in self.form:
            try:
                self.embedded = bool(int(self.form['@embedded']))
            except ValueError:
                pass
        return chart
    
    
    def get_sample_data_from_query(self, db, classname=None, filterspec=None,
                        group=None, search_text=None, **other):
        """Parse and summarize the query submitted into a data table."""
        cl = db.getclass(classname)
        data = defaultdict(lambda: defaultdict(int))  # Initialize defaultdict for storing data
        
        # Full-text search
        if search_text:
            matches = db.indexer.search(re.findall(r'\b\w{2,25}\b', search_text), cl)
        else:
            matches = None

        # Iterate through issues and count occurrences of status within each title category
        issues = cl.filter(matches, filterspec, sort=[('+', 'id')], group=group)
        for nodeid in issues:
            if not self.hasPermission('View', itemid=nodeid, classname=cl.classname):
                continue
            title_id = cl.get(nodeid, 'priority')  # Get the priority of the issue
            status_id = cl.get(nodeid, 'status')  # Get the status of the issue
            title = db.getclass('priority').get(title_id, 'name')  # Get the name of the priority
            status = db.getclass('status').get(status_id, 'name')
            data[title][status] += 1  # Increment count for the specific title and status

        # Convert defaultdict to standard dictionary
        data = dict(data)
        for title, status_count in data.items():
            data[title] = dict(status_count)
        return data
    
    def plot_data(self, data, arg, chart):
        # add a link to each data point. Clicking it will filter
        # down to the issued in that slice/bar.
        # Remove and replace the @filter url param. Only
        # the last one is used. So we add the property used for
        # grouping to the existing filter and generate the new
        # url.
        current_filter = arg['request'].filter
        arg['request'].filter = None  # erase filter
        # get new url without filter
        current_url = arg['request'].current_url()
        # get grouping property name
        gprop = arg['group'][0][1]
        # generate a new @filter value adding the gprop
        filter = ','.join(current_filter + [gprop])
        for d in data:
            xlink = {'target': '_blank',
                     'href': current_url +
                     "&@filter=%(filter)s&%(gprop)s=%(gval)s" % {
                         'gprop': gprop,
                         'gval': d[0] if d[0] != "Unassigned" else -1,
                         'filter': filter,
                     }}

            chart.add(d[0], [{'value': d[1], 'xlink': xlink}])

        return
    
    def plot_data_for_Stackedbar_Chart(self, data, arg, chart):

        # Rearrange data structure to have statuses as keys and issue types with their counts as values
        status_data = defaultdict(dict)
        for issue_type, status_counts in data.items():
            for status, count in status_counts.items():
                status_data[status][issue_type] = count

        
        # Add statuses as categories and issue types with their counts as stacks
        for status, issue_counts in status_data.items():
            chart.add(status, issue_counts)
        
        return


    def pygal_add_nonce(self):
        """Modify the pygal style and script methods to add a nonce
           so it will work under a CSP.
        """

        # modify svg to add nonces so styles and scripts will run
        pgSvg_add_styles = pygal.svg.Svg.add_styles
        pgSvg_add_scripts = pygal.svg.Svg.add_scripts

        def new_add_styles(self, *args, **named_args):
            pgSvg_add_styles(self, *args, **named_args)
            if hasattr(self.graph, "nonce"):  # add the nonce if it exists
                for style in self.root.find('defs').findall('style'):  # there is only one currently
                    style.set('nonce', self.graph.nonce)

        def new_add_scripts(self, *args, **named_args):
            pgSvg_add_scripts(self, *args, **named_args)
            if hasattr(self.graph, "nonce"):  # add the nonce if it exists
                # there are two or more depending on self.graph.js.
                for script in self.root.find('defs').findall('script'):
                    script.set('nonce', self.graph.nonce)

        pygal.svg.Svg.add_styles = new_add_styles
        pygal.svg.Svg.add_scripts = new_add_scripts


class PieChartAction(ChartingAction):
    """Generate a pie chart from the result of an index query. Sum items
       per group.
    """

    def handle(self):
        ''' Show chart for current query results
        '''
        db = self.db

        # 'arg' will contain all the data that we need to pass to
        # the data retrival step.
        arg = {}

        # needed to get the query data
        request = templating.HTMLRequest(self.client)

        arg['request'] = request

        arg['classname'] = request.classname

        if request.filterspec:
            arg['filterspec'] = request.filterspec

        if request.group:
            # assumption is that this is a list of tuples for most
            # cases
            arg['group'] = request.group

        if request.search_text:
            arg['search_text'] = request.search_text

        # execute the query again and count grouped items
        # data looks like list of (grouped_label, count):
        '''
          data = [ ("admin", 25),
                 ("demo", 15),
                 ("agent", 45),
                 ("provisional", 65),
                 ]
        '''
        data = self.get_data_from_query(db, **arg)

        if not data:
            raise ValueError("Failed to obtain data for graph.")

        # For Pie chart, sort by count. Largest first.
        data.sort(key=lambda i: i[1], reverse=True)

        # build image here

        config = pygal.Config()

        # Customize CSS
        # Almost all font-* here needs to be !important. Base styles include
        #  the #custom-chart-anchor which gives the base setting higher
        #  specificy/priority.  I don't know how to get that value so I can
        #  add it to the rules. I suspect with code reading I could set some
        #  of these using pygal.style....
        # Also with background and plot_background Style set to transparent
        #  (so it can be displayed in an html temlpate) the tooltip
        #  fill needs to be explicitly set to white.

        # make plot title larger and wrap lines
        config.css.append('''inline:
          g.titles text.plot_title {
            font-size: 20px !important;
            white-space: pre-line;
          }''')
        config.css.append('''inline:
          g.legend text {
            font-size: 8px !important;
            white-space: pre-line;
          }''')
        # make background of popup label solid.
        config.css.append('''inline:
          g.tooltip .tooltip-box {
            fill: #fff !important;
          }''')

        cstyle = pygal.style.Style(background='transparent',
                                   plot_background='transparent')

        if self.jsURL:
            config.js[0] = self.jsURL

        self.pygal_add_nonce()

        chart = pygal.Pie(config,
                          width=400,
                          height=400,
                          style=cstyle,
                          print_values=True,
                          # make embedding easier
                          disable_xml_declaration=True,
                          )

        chart.nonce = self.client.client_nonce

        self.plot_data(data, arg, chart)

        # WARN this will break if group is not list of tuples
        chart.title = "Tickets grouped by %s \n(%s)" % (arg['group'][0][1],
                                                        db.config.TRACKER_NAME)

        headers = self.client.additional_headers
        headers['Content-Type'] = self.output_type

        if self.output_type == 'image/svg+xml':
            image = chart.render(is_unicode=True, pretty_print=True)
            headers['Content-Disposition'] = 'inline; filename=pieChart.svg'
        elif self.output_type == 'image/png':
            image = chart.render_to_png()
            headers['Content-Disposition'] = 'inline; filename=pieChart.png'
            # with open('/tmp/image.png', 'rb') as infile:
            #    image=infile.read()
        elif self.output_type == 'data:':
            image = chart.render_data_uri(is_unicode=True)
        else:
            raise ValueError("Unknown pygal output type: %s" %
                             self.output_type)
        
        chart_data = {'image',bs2b(image)}
        #print(chart_data)

        #return bs2b(image)  # send through Client.write_html()
        # from django.shortcuts import render
        # return render(request,'issue.chart.html',{'image':bs2b(image)}))
        return bs2b(image)
    


class BarChartAction(ChartingAction):
    """Generate a bar chart from the result of an index query. Sum items
       per group.
    """

    # set output image type. svg is interactive
    output_type = "image/svg+xml"
    # output_type = 'image/png'

    def handle(self):
        ''' Show chart for current query results
        '''
        db = self.db

        # 'arg' will contain all the data that we need to pass to
        # the data retrival step.
        arg = {}

        # needed to get the query data
        request = templating.HTMLRequest(self.client)

        arg['request'] = request

        arg['classname'] = request.classname

        if request.filterspec:
            arg['filterspec'] = request.filterspec

        if request.group:
            # assumption is that this is a list of tuples for most
            # cases
            arg['group'] = request.group

        if request.search_text:
            arg['search_text'] = request.search_text

        # execute the query again and count grouped items
        # data looks like list of (grouped_label, count):
        '''
          data = [ ("admin", 25),
                 ("demo", 15),
                 ("agent", 45),
                 ("provisional", 65),
                 ]
        '''
        data = self.get_data_from_query(db, **arg)

        if not data:
            raise ValueError("Failed to obtain data for graph.")

        # build image here

        config = pygal.Config()
        # Customize CSS
        # Almost all font-* here needs to be !important. Base styles include
        #  the #custom-chart-anchor which gives the base setting higher
        #  specificy/priority.  I don't know how to get that value so I can
        #  add it to the rules. I suspect with code reading I could set some
        #  of these using pygal.style....

        # make plot title larger and wrap lines
        config.css.append('''inline:
          g.titles text.plot_title {
            font-size: 20px !important;
            white-space: pre-line;
          }''')
        config.css.append('''inline:
          g.legend text {
            font-size: 8px !important;
            white-space: pre-line;
          }''')
        # make background of popup label solid.
        config.css.append('''inline:
          g.tooltip .tooltip-box {
            fill: #fff !important;
          }''')

        cstyle_barchart=pygal.style.Style(background='transparent',
                          plot_background='transparent')

        if self.jsURL:
            config.js[0] = self.jsURL

        self.pygal_add_nonce()

        chart = pygal.Bar(config,
                          width=400,
                          height=400, 
                          style=cstyle_barchart,
                          print_values=True,
                          # make embedding easier
                          disable_xml_declaration=True,
                          )

        chart.nonce = self.client.client_nonce
        self.plot_data(data, arg, chart)

        # WARN this will break if group is not list of tuples
        chart.title = "Tickets grouped by %s \n(%s)" % (arg['group'][0][1],
                                                        db.config.TRACKER_NAME)

        headers = self.client.additional_headers
        headers['Content-Type'] = self.output_type

        if self.output_type == 'image/svg+xml':
            image = chart.render(is_unicode=True, pretty_print=True)
            headers['Content-Disposition'] = 'inline; filename=pieChart.svg'
        elif self.output_type == 'image/png':
            image = chart.render_to_png()
            headers['Content-Disposition'] = 'inline; filename=pieChart.png'
            # with open('/tmp/image.png', 'rb') as infile:
            #    image=infile.read()
        elif self.output_type == 'data:':
            image = chart.render_data_uri(is_unicode=True)
        else:
            raise ValueError("Unknown pygal output type: %s" %
                             self.output_type)

        return bs2b(image)  # send through Client.write_html()
    

class StackedBarChartAction(ChartingAction):
    """Generate a stacked bar chart from the result of an index query. Sum items
       per group and stack by status.
    """

    # set output image type. svg is interactive
    output_type = "image/svg+xml"
    # output_type = 'image/png'

    def handle(self):
        ''' Show chart for current query results
        '''
        db = self.db

        # 'arg' will contain all the data that we need to pass to
        # the data retrieval step.
        arg = {}

        # Needed to get the query data
        request = templating.HTMLRequest(self.client)

        arg['request'] = request
        arg['classname'] = request.classname

        if request.filterspec:
            arg['filterspec'] = request.filterspec

        if request.group:
            arg['group'] = request.group

        if request.search_text:
            arg['search_text'] = request.search_text
        

        # Execute the query again and count grouped items
        data = self.get_sample_data_from_query(db, **arg)

        if not data:
            raise ValueError("Failed to obtain data for graph.")

        # build image here

        config = pygal.Config()
        # Customize CSS
        # Almost all font-* here needs to be !important. Base styles include
        #  the #custom-chart-anchor which gives the base setting higher
        #  specificy/priority.  I don't know how to get that value so I can
        #  add it to the rules. I suspect with code reading I could set some
        #  of these using pygal.style....

        # make plot title larger and wrap lines
        config.css.append('''inline:
          g.titles text.plot_title {
            font-size: 20px !important;
            white-space: pre-line;
          }''')
        config.css.append('''inline:
          g.legend text {
            font-size: 8px !important;
            white-space: pre-line;
          }''')
        # make background of popup label solid.
        config.css.append('''inline:
          g.tooltip .tooltip-box {
            fill: #fff !important;
          }''')
        
        pygal.style.Style(background='transparent',
                          plot_background='transparent')

        if self.jsURL:
            config.js[0] = self.jsURL

        self.pygal_add_nonce()
        
        chart = pygal.StackedBar(config,
                          width=400,
                          height=400,
                          print_values=True,
                          # make embedding easier
                          disable_xml_declaration=True,
                          )
        
        chart.nonce = self.client.client_nonce
        self.plot_data_for_Stackedbar_Chart(data, arg, chart)

        # Give a title 
        chart.title = "Tickets grouped by Priority and Status"

        headers = self.client.additional_headers
        headers['Content-Type'] = self.output_type

        # Set labels for the x-axis
        chart.x_labels = list(data.keys())

        # Render the chart and return the SVG image
        image = chart.render()
        #headers['Content-Disposition'] = 'inline; filename=stackedChart.svg'

        return bs2b(image)
 
def init(instance):
    instance.registerAction('piechart', PieChartAction)
    instance.registerAction('barchart', BarChartAction)
    instance.registerAction('stackedchart', StackedBarChartAction)
