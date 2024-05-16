import pygal
import re
import gettext

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
    # jsURL = "https://rouilj.dynamic-dns.net/sysadmin/@@file/jslibraries/pygal-tooltips.js"

    # set output image type. svg and data: are interactive
    output_type = "image/svg+xml"  # @image_type: image/svg+xml, image/png, data:

    # image is to be embedded in a rendered html page rather than stand alone.
    embedded = False  # @embedded: 0, 1

    def set_jsURL(self):
               # original source_url:
      #  "https://kozea.github.io/pygal.js/2.0.x/pygal-tooltips.js"
       # Use our local copy of pygal-tooltips.js
       try:
           relative_jsURL = self.db.config.ext['CHART_JSURL']
        except KeyError:
            relative_jsURL = "pygal-tooltips.js"

       if relative_jsURL:
            self.jsURL = "%s@@file/%s" % (self.db.config['TRACKER_WEB'],
                                          relative_jsURL)

    def get_data_from_query(self, db, classname=None, filterspec=None,
                            group=None, search_text=None, **other):
        """Parse and summarize the query submitted into a data table.
        Also look for @image_type= and set output_type appropriately
        and @embedded (boolean) and set it properly. Embedded not yet used.
        """

        # Get the class from the database
        cl = db.getclass(classname)
        log.append('cl=%s' % cl)

        # Full-text search
        if search_text:
            matches = db.indexer.search(re.findall(r'\b\w{2,25}\b',
                                                search_text), cl)
        else:
            matches = None
        log.append('matches=%s' % matches)

        # If group is a list and has one property, extract first property ...
        if(len(group)==1):
            # Extract the first group property name
            first_group_propname = group[0][1]
            log.append('first_group_propname=%s' % first_group_propname)

            # Get the property type of the first group property
            try:
                first_prop_type = cl.getprops()[first_group_propname]
                log.append('first_prop_type=%s' % first_prop_type)
            except KeyError:
                raise ValueError(
                    'Charts can only be created on '
                    'Linked properties!\n %s is not '
                    'a Linked property\n' % first_group_propname)

            # Check if the property type is a link, multilink or Boolean
            if not isinstance(first_prop_type, hyperdb.Link) \
                and not isinstance(first_prop_type, hyperdb.Multilink):
                    raise ValueError(
                        'Charts can only be created on '
                        'Linked properties!\n %s is not '
                        'a Linked property\n' % first_group_propname)
                    return

            

            # Initialize property dictionary
            props = {}

            if not filterspec:
                filterspec = {}

            # Filter issues based on matches and filterspec
            issues = cl.filter(matches, filterspec, sort=[('+', 'id')],
                            group=group)

            log.append('issues=%s' % issues)

            # Count occurrences of each property value
            # Get the class for the property type
            klass = db.getclass(first_prop_type.classname)
            log.append('klass=%s' % klass)

            for nodeid in issues:
                if not self.hasPermission('View', itemid=nodeid,
                                        classname=cl.classname):
                    continue
                prop_ids = cl.get(nodeid, first_group_propname)
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

            # Convert property dictionary to list of tuples
            chart = [(k, v) for k, v in props.items()]

            # Set output type if specified in form
            if '@image_type' in self.form:
                self.output_type = self.form['@image_type'].value

            # Set embedded flag if specified in form
            if '@embedded' in self.form:
                try:
                    self.embedded = bool(int(self.form['@embedded']))
                except ValueError:
                    pass

            return chart

        # If group is a list and has two properties, extract both properties ...
        else:
            data = defaultdict(lambda: defaultdict(int))  # Initialize defaultdict for storing data
            first_group_propname = group[0][1]
            second_group_propname = group[1][1]

            # Get the property types for the two group properties
            try:
                first_prop_type = cl.getprops()[first_group_propname]
            except KeyError:
                raise ValueError(
                    'Charts can only be created on '
                    'Linked properties!\n %s is not '
                    'a Linked property\n' % first_group_propname)
            
            if not isinstance(first_prop_type, hyperdb.Link) \
            and not isinstance(first_prop_type, hyperdb.Multilink):
                raise ValueError(
                    'Charts can only be created on '
                    'Linked properties!\n %s is not '
                    'a Linked property\n' % first_group_propname)
                return

            try:
                second_prop_type = cl.getprops()[second_group_propname]
            except KeyError:
                raise ValueError(
                    'Charts can only be created on '
                    'Linked properties!\n %s is not '
                    'a Linked property\n' % second_group_propname)

            if not isinstance(second_prop_type, hyperdb.Link) \
            and not isinstance(second_prop_type, hyperdb.Multilink):
                raise ValueError(
                    'Charts can only be created on '
                    'Linked properties!\n %s is not '
                    'a Linked property\n' % second_group_propname)
                return

            # Iterate through issues and count occurrences of each property value combination
            issues = cl.filter(matches, filterspec, sort=[('+', 'id')], 
                               group=group)
            
            # set the key value and class name based on the property type
            key1 = db.getclass(first_prop_type.classname).getkey()
            key2 = db.getclass(second_prop_type.classname).getkey()
            class1 = db.getclass(first_prop_type.classname)
            class2 = db.getclass(second_prop_type.classname)

            for nodeid in issues:
                if not self.hasPermission('View', itemid=nodeid, classname=cl.classname):
                    continue
                    
                first_prop_ids = cl.get(nodeid, first_group_propname)
                second_prop_ids = cl.get(nodeid, second_group_propname)

                # Function to handle counting based on property values
                def count_property_value(prop_value, class_get_func, key):
                    return class_get_func(prop_value, key)

                # Check and process first property
                if first_prop_ids:
                    if not isinstance(first_prop_ids, list):
                        first_prop_ids = [first_prop_ids]
                    for first_prop_id in first_prop_ids:
                        first_prop_value = count_property_value(first_prop_id, class1.get, key1)
                        # Check and process second property
                        if second_prop_ids:
                            if not isinstance(second_prop_ids, list):
                                second_prop_ids = [second_prop_ids]
                            for second_prop_id in second_prop_ids:
                                second_prop_value = count_property_value(second_prop_id, class2.get, key2)
                                data[first_prop_value][second_prop_value] += 1
                        else:
                            second_prop_value = "Unassigned"
                            data[first_prop_value][second_prop_value] += 1
                else:
                    first_prop_value = "Unassigned"
                    # Check and process second property
                    if second_prop_ids:
                        if not isinstance(second_prop_ids, list):
                            second_prop_ids = [second_prop_ids]
                        for second_prop_id in second_prop_ids:
                            second_prop_value = count_property_value(second_prop_id, class2.get, key2)
                            data[first_prop_value][second_prop_value] += 1
                    else:
                        second_prop_value = "Unassigned"
                        data[first_prop_value][second_prop_value] += 1

            # Convert defaultdict to standard dictionary
            data = dict(data)
            for first_prop, second_prop_count in data.items():
                data[first_prop] = dict(second_prop_count)
            
            # Set output type if specified in form
            if '@image_type' in self.form:
                self.output_type = self.form['@image_type'].value

            # Set embedded flag if specified in form
            if '@embedded' in self.form:
                try:
                    self.embedded = bool(int(self.form['@embedded']))
                except ValueError:
                    pass
            
            return data

    
    def plot_data(self, data, arg, chart, level_of_grouping):
        """
        Add a link to each data point. Clicking it will filter down to the issues in that slice/bar.
        Remove and replace the @filter url param. Only the last one is used. So we add the property used for
        grouping to the existing filter and generate the new url.
        """
        current_filter = arg['request'].filter
        arg['request'].filter = None  # erase filter
        # Get the current URL without filter
        current_url = arg['request'].current_url()
        
        if len(arg['group']) == 1 and level_of_grouping == 1:
            # get grouping property name
            gprop = arg['group'][0][1]
            # generate a new @filter value adding the gprop
            filter = ','.join(current_filter + [gprop])
            for d in data:
                # Generate xlink for each data point
                xlink = {
                    'target': '_parent',
                    'href': current_url + 
                    "&@filter=%(filter)s&%(gprop)s=%(gval)s" % {
                        'gprop': gprop,
                        'gval': d[0] if d[0] != "Unassigned" else -1,  # Handle "Unassigned" case
                        'filter': filter,
                    }
                }
                # print(xlink)
                # Add data point to chart with xlink
                chart.add(d[0], [{'value': d[1], 'xlink': xlink}])
        
        elif len(arg['group']) == 2 and level_of_grouping == 2:
            # For two-level grouping
            grouping_props = [arg['group'][0][1], arg['group'][1][1]]
            if isinstance(grouping_props, list):
                new_filter = ','.join(grouping_props)
            
            # Rearrange data structure to have second property as keys and first property with their counts as values
            second_prop_data = defaultdict(dict)
            for first_prop, first_prop_counts in data.items():
                for second_prop, second_prop_count in first_prop_counts.items():
                    second_prop_data[second_prop][first_prop] = second_prop_count        
            
            for second_prop, second_prop_counts in second_prop_data.items():
                # Create a dictionary to store data for the current second_prop
                second_prop_dict = {}
                for first_prop, count in second_prop_counts.items():
                    # Generate link for the current second_prop and first_prop
                    xlink = {
                        'target': '_parent',
                        'href': current_url + "&@filter=%(filter)s&%(first_prop)s=%(first_prop_val)s&%(second_prop)s=%(second_prop_val)s" % {
                            'filter': new_filter,
                            'first_prop': grouping_props[0],  # Assuming the property name for first_prop
                            'first_prop_val': first_prop,  # Get first_prop value from the loop
                            'second_prop': grouping_props[1],  # Assuming the property name for second_prop
                            'second_prop_val': second_prop,
                        }
                    }
                    # Add count and xlink to the inner dictionary for the current first_prop
                    second_prop_dict[first_prop] = {'count': count, 'xlink': xlink}
                # Add the inner dictionary to the chart
                chart.add(second_prop, [{'value': data['count'], 'xlink': data['xlink']} for first_prop, data in second_prop_dict.items()])
        
        else:
            # Print message if appropriate chart and grouping not selected
            print("Select appropriate chart and grouping")
        
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
        self.set_jsURL()
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
        
        if len(arg['group']) > 1:
            raise ValueError("Remove second level of grouping to see piechart")

        if request.search_text:
            arg['search_text'] = request.search_text

        if request.sort:
            arg['sort'] = request.sort

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

        sort_param = arg.get('sort')
        if sort_param is not None and '-' in sort_param[0]:
            data.sort(key=lambda i: i[1], reverse=True)
        else:
            data.sort(key=lambda i: i[1])

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
        level_of_grouping = 1
        self.plot_data(data, arg, chart, level_of_grouping)

        # WARN this will break if group is not list of tuples
        chart.title = db.i18n.gettext("Tickets grouped by %(propertyName)s \n(%(trackerName)s)"
                                       %{
                                           'propertyName': db.i18n.gettext(arg['group'][0][1]),
                                           'trackerName' : db.config.TRACKER_NAME
                                       } )
        

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
        self.set_jsURL()
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

        if len(arg['group']) > 1:
            raise ValueError("Remove second level of grouping to see Barchart")

        if request.search_text:
            arg['search_text'] = request.search_text

        if request.sort:
            arg['sort'] = request.sort

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
        
        sort_param = arg.get('sort')
        if sort_param is not None and '-' in sort_param[0]:
            data.sort(key=lambda i: i[1], reverse=True)
        else:
            data.sort(key=lambda i: i[1])

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

        cstyle_barchart= pygal.style.Style(background='transparent',
                          plot_background='transparent')

        if self.jsURL:
            config.js[0] = self.jsURL

        self.pygal_add_nonce()

        chart = pygal.Bar(config,
                          width=400,
                          height=400,
                          style = cstyle_barchart,
                          print_values=True,
                          # make embedding easier
                          disable_xml_declaration=True,
                          )

        chart.nonce = self.client.client_nonce
        level_of_grouping = 1
        self.plot_data(data, arg, chart, level_of_grouping)

        # # WARN this will break if group is not list of tuples
        chart.title = db.i18n.gettext("Tickets grouped by %(propertyName)s \n(%(trackerName)s)"
                                       %{
                                           'propertyName': db.i18n.gettext(arg['group'][0][1]),
                                           'trackerName' : db.config.TRACKER_NAME
                                       } )

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
    


class HorizontalBarChartAction(ChartingAction):
    """Generate a bar chart from the result of an index query. Sum items
       per group.
    """

    # set output image type. svg is interactive
    output_type = "image/svg+xml"
    # output_type = 'image/png'

    def handle(self):
        ''' Show chart for current query results
        '''
        self.set_jsURL()
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

        if len(arg['group']) > 1:
            raise ValueError("Remove second level of grouping to see Horizontal Barchart")

        if request.search_text:
            arg['search_text'] = request.search_text

        if request.sort:
            arg['sort'] = request.sort

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

        sort_param = arg.get('sort')
        if sort_param is not None and '-' in sort_param[0]:
            data.sort(key=lambda i: i[1], reverse=True)
        else:
            data.sort(key=lambda i: i[1])

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

        chart = pygal.HorizontalBar(config,
                          width=400,
                          height=400,
                          print_values=True,
                          style = cstyle_barchart,
                          # make embedding easier
                          disable_xml_declaration=True,
                          y_title=arg['group'][0][1]
                          )


        chart.nonce = self.client.client_nonce
        level_of_grouping = 1
        self.plot_data(data, arg, chart, level_of_grouping)
        # WARN this will break if group is not list of tuples
        
        chart.title = db.i18n.gettext("Tickets grouped by %(propertyName)s \n(%(trackerName)s)"
                                       %{
                                           'propertyName': db.i18n.gettext(arg['group'][0][1]),
                                           'trackerName' : db.config.TRACKER_NAME
                                       } )


        headers = self.client.additional_headers
        headers['Content-Type'] = self.output_type

        # Render the chart and return the SVG image
        image = chart.render()

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
        self.set_jsURL()
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

        if len(arg['group']) < 2:
            raise ValueError("Select second level of grouping to see Stacked Barchart")

        if request.search_text:
            arg['search_text'] = request.search_text
        
        # execute the query again and count grouped items
        # data looks like below:
        '''
          data = [ {Critical: ("urgent", 25),
                 ("ready", 15)},
                 {Normal: ("agent", 45),
                 ("provisional", 65)}
                 ]
        '''
        # Execute the query again and count grouped items
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
        
        chart = pygal.StackedBar(config,
                          width=400,
                          height=400,
                          style = cstyle_barchart,
                          print_values=False,
                          # make embedding easier
                          disable_xml_declaration=True,
                          x_title=arg['group'][0][1]
                          )
        
        chart.nonce = self.client.client_nonce
        level_of_grouping = 2
        self.plot_data(data, arg, chart, level_of_grouping)

        # Give a title 

        chart.title = db.i18n.gettext("Tickets grouped by %(propertyName1)s and %(propertyName2)s \n(%(trackerName)s)"
                                       %{
                                           'propertyName1': db.i18n.gettext(arg['group'][0][1]),
                                           'propertyName2': db.i18n.gettext(arg['group'][1][1]),
                                           'trackerName' : db.config.TRACKER_NAME
                                       } )
        # Set labels for the x-axis
        chart.x_labels = list(data.keys())

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

        return bs2b(image)
    

    
class MultiBarChartAction(ChartingAction):
    """Generate a multi-bar chart from the result of an index query. 
        Each group represents a separate bar.
    """

    # set output image type. svg is interactive
    output_type = "image/svg+xml"
    # output_type = 'image/png'

    def handle(self):
        ''' Show chart for current query results
        '''
        self.set_jsURL()
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

        if len(arg['group']) < 2:
            raise ValueError("Select second level of grouping to see  MultiBarchart")

        if request.search_text:
            arg['search_text'] = request.search_text
        
        # execute the query again and count grouped items
        # data looks like below:
        '''
          data = [ {Critical: ("urgent", 25),
                 ("ready", 15)},
                 {Normal: ("agent", 45),
                 ("provisional", 65)}
                 ]
        '''
        # Execute the query again and count grouped items
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
            font-size: 18px !important;
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
                          width=500,
                          height=400,
                          style = cstyle_barchart,
                          print_values=False,
                          # make embedding easier
                          disable_xml_declaration=True,
                          x_title=arg['group'][0][1]
                          )
        
        chart.nonce = self.client.client_nonce
        level_of_grouping = 2
        self.plot_data(data, arg, chart, level_of_grouping)
        # Give a title 
        
        chart.title = db.i18n.gettext("Tickets grouped by %(propertyName1)s and %(propertyName2)s \n(%(trackerName)s)"
                                       %{
                                           'propertyName1': db.i18n.gettext(arg['group'][0][1]),
                                           'propertyName2': db.i18n.gettext(arg['group'][1][1]),
                                           'trackerName' : db.config.TRACKER_NAME
                                       } )

        # Set labels for the x-axis
        chart.x_labels = list(data.keys())

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

        return bs2b(image)


 
def init(instance):
    instance.registerAction('piechart', PieChartAction)
    instance.registerAction('barchart', BarChartAction)
    instance.registerAction('stackedchart', StackedBarChartAction)
    instance.registerAction('multibarchart', MultiBarChartAction)
    instance.registerAction('horizontalbarchart', HorizontalBarChartAction)

