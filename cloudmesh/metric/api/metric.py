import sys
from tabulate import tabulate
import requests
from collections import OrderedDict

class metric_api:

    def __init__(self):
        self.from_date = None
        self.to_date = None
        self.period = None
        self.timetype = None
        self.metric = None
        self.cluster = None
        self.iaas = None
        self.userid = None

        self.set_default()
        self.load_server_info()

    def __str__(self):
        result = ""
        result += "from_date: %s\n" % self.from_date
        result += "to_date:   %s\n" % self.to_date
        result += "period:    %s\n" % self.period
        result += "timetype:    %s\n" % self.timetype
        result += "metric:    %s\n" % self.metric
        result += "cluster:   %s\n" % self.cluster
        result += "iaas:      %s\n" % self.iaas
        result += "userid:      %s\n" % self.userid
        return result

    def set_default(self):
        self.timetype = "hour"
        self.metric = "vmcount"

    def load_server_info(self):
        # cloudmesh_server.yaml contains the api server info
        # this is only for test.
        self.host = "156.56.93.202"
        self.port = 5001
        self.doc_url = "metric"
 
    def connect(self):
        try:
            print self.get_uri()
            r = requests.get(self.get_uri())
            return r.json()
        except requests.ConnectionError:
            print "Connection failed to %s" % self.get_uri()
        except requests.HTTPError as e:
            print "Invalid HTTP response ({0},{1})".format(e.errno, e.strerror)
        except requests.Timeout:
            print "HTTP times out"
        except requests.TooManyRedirects:
            print "Exceeds the configured number of maximum redirections"
        except:
            print "Unexpected error:", sys.exc_info()[0]
            raise

    def get_uri(self):
        # /metric/<cloudname>/<clustername>/<username>/<metric>/<timestart>/<timeend>/<period>
        uri = ["http:/"]
        uri.append(self.host + ":" + str(self.port))
        uri.append(self.doc_url)
        uri.append(self.iaas)
        uri.append(self.cluster)
        uri.append(self.userid)
        uri.append(self.metric)
        uri.append(self.from_date)
        uri.append(self.to_date)
        uri.append(self.period)
        self.uri = "/".join(map(str,uri))
        return self.uri
    
    def set_date(self, from_date, to_date):
        # NOT IMPLEMENTED MESSAGE
        if from_date:
            self.na_message(sys._getframe().f_code.co_name, from_date, to_date)

        self.from_date = from_date
        self.to_date = to_date

    def set_period(self, period):
        # NOT IMPLEMENTED MESSAGE
        if period:
            self.na_message(sys._getframe().f_code.co_name, period)

        self.period = period

    def set_metric(self, metric):
        if metric:
            self.metric = metric

    def set_cluster(self, cluster):
        # NOT IMPLEMENTED MESSAGE
        if cluster:
            self.na_message(sys._getframe().f_code.co_name, cluster)

        self.cluster = cluster

    def set_iaas(self, cloud):
        self.iaas = cloud

    def set_cloud(self, cloud):
        ''' link to set_iaas '''
        self.set_iaas(cloud)

    def set_user(self, userid):
        # NOT IMPLEMENTED MESSAGE
        if userid:
            self.na_message(sys._getframe().f_code.co_name, userid)

        self.userid = userid

    def test_raw_data(self):
        # for test, dummy data is returned
        res = [["HOST", "PROJECT", "cpu", "memory_mb", "disk_gb"],
               ["india","(total)",2, 4003,157],
               ["india","(used_now)", 3, 5120, 40],
               ["india","(used_max)",3,4608, 40],
               ["india","b70d90d65e464582b6b2161cf3603ced",1,512,0],
               ["india","66265572db174a7aa66eba661f58eb9e",2,4096,40]]
        return res
 
    def get_raw_data(self):
        # expect list variable
        res = self.connect()
        # res is dict
        dictlist = []
        i = 0
        for row in res["message"]:
            if i == 0:
                dictlist.append(row.keys())
            i=1
            dictlist.append(row.values())
        self.raw_data = dictlist

        self.comparison_table(res)

    def translate_naming(self, name):
        name = name.upper()

        if name in ["WALLTIME", "WALLCLOCK", "RUNTIME"]:
            timetype = self.translate_naming(self.timetype)
            return "WallTime ("+timetype+")"
        elif name == "HOUR":
            return "Hrs"
        else:
            return name

    def comparison_table(self, res):
        # Let's provide comparison table if there is no search option defined
        if self.userid or self.iaas or self.cluster:
            return

        # New table for the comparison of IaaS
        # ====================================
        distlist_comparison = []
        index = "YEAR MONTH"
        column = "CLOUDNAME"
        value = self.translate_naming(name = self.metric)#"VMCOUNT")
       
        iaas = []
        dates = []
        for row in res["message"]:
            try:
                iaas.index(row[column])
            except ValueError:
                iaas.append(row[column])
            try:
                dates.index(row[index])
            except ValueError:
                dates.append(row[index])

        # header for the new table
        distlist_comparison.append(["DATE"] + iaas)
        complist = OrderedDict()
        for row in res["message"]:
            # date | openstack | eucalyptus | nimbus
            pos = iaas.index(row[column])
            try:
                complist[row[index]][pos] = row[value]
            except KeyError:
                complist[row[index]] = [0]*len(iaas)
                complist[row[index]][pos] = row[value]

        for k, v in complist.iteritems():
            distlist_comparison.append([k]+v)

        self.raw_data = distlist_comparison

    def display(self, table_format="orgtbl"):
        # table_format = 
        # plain,
        # simple,
        # grid,
        # pipe,
        # orgtbl,
        # rst,
        # mediawiki,
        # latex
        self.table = tabulate (self.raw_data, headers="firstrow",
                               tablefmt=table_format)
        seperator = self.table.split("\n")[1].replace("|", "+")
        print seperator
        print self.table
        print seperator        
        
    def get_stats(self):
        #print vars(self)
        self.get_raw_data()
        self.display()
        return

    def stats(self):
        ''' link to get_stats '''
        return self.get_stats()

    def na_message(self, func_name, *args):
        args = map(str,args)
        msg = "%s is not implemented, '%s' ignored." % \
                ( func_name, ', '.join(args))
        print "=" * len(msg)
        print msg
        print "=" * len(msg)
        print

