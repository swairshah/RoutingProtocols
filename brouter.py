import sys
import os.path
from time import sleep,localtime,strftime,time
from graph import Graph
from irouter import irouter

class brouter(irouter):
    def __init__(self,args):
        self.ID, self.AS, self.addrs = self.parse_args(args)

        self.old_bids = {} # node_id : bid
        self.old_bid_timers = {} # node_id : time at last bid
        self.nets = [i[0] for i in self.addrs]
        self.readers = []

        self.g = Graph()
        self.g.add_node(self.ID,self.nets)
        #self.g.print_graph()

        #broadcast id
        self.bid = 0

        for i in self.nets:
            fname = 'net/NET'+i
            f = open(fname,'r')
            self.readers.append(f)

        self.file = 'host/out'+self.ID
        self.routing = 'rt/rt'+self.ID

        #brouter stuff
        self.other_as_brouters = {} # as:[ids]
        self.my_as_brouters = []

        self.paths_from_other_as = {}
        self.paths_from_my_as = {}
        self.paths_from_peers = {}
        self.paths_from_customers = {}
        self.paths_from_providers = {}

        self.networks_in_as = {}

        self.peers = []
        self.customers = []
        self.providers = []

        self.parse_relations()


    def parse_relations(self):
        try:
            f = open("HBGP.txt",'r')
            for line in f.readlines():
                if not self.AS in line:
                    continue
                if '-->' in line:
                    as1, as2 = line.split('-->')
                    if as1 == self.AS:
                        self.customers.append(as2.strip())
                    else:
                        self.providers.append(as1.strip())

                else:
                    if '-' in line:
                        as1, as2 = line.split('-')
                        if as1 == self.AS:
                            self.peers.append(as2.strip())
                        else:
                            self.peers.append(as1.strip())
        except:
            print "no HBGP file"

    def do_bgpa(self):
        for AS,br_tuples in self.other_as_brouters.iteritems():
            if AS in self.customers:
                self.bgpa_customer_routes(self,AS,br_tuples)

    def bgpa_customers_routes(AS, br_tuples):
        if self.paths_from_customers == {}:
            return

        for br_id, br_addr in brs:
            nn = br_addr[0]
            msg_dst = br_addr[0]+' '+br_addr[1]
            for path_dst,path_tuple in self.paths_from_customers:
                path = path_tuple[0]
                path = path.append(self.AS)

                networks = self.networks_in_as[path[-1]]
                networks = ' '.join(networks)

                path = ' '.join(path) 

                for ip_addr in self.addrs:
                    if ip_addr[0] == nn:
                        msg_src = ip_addr[0]+' '+ip_addr[1]
                        bgpa_msg = msg_src+' '+msg_dst+' '+self.ID+' PATHADV '+path+' NETWKS '+ networks

                        print bgpa_msg
    
    def parse_args(self,args):
        """
        takes the whole argument string, (sys.argv)
        returns id,AS,list_of_(nn,hh)
        """
        if len(args) < 4:
            raise Exception("check the arguments you passed!")
        ID = args[1]
        AS = args[2]
        ip_addrs = list()

        addr_num = len(args[3:])
        if addr_num % 2 != 0:
            raise Exception("seems like nn,hh pairs are not complete!")

        for i in xrange(1,addr_num/2+1):
            nn = args[i*2+1]
            hh = args[i*2+2]
            ip_addrs.append(tuple([nn,hh]))

        return ID,AS,ip_addrs

    def process(self, msg):
        """
        msg example:
        (10,02) (08,99) LSA 13 05 NETWKS 10 04 01 03 11 OPTIONS BORDER 05 INJECTED  03 11
        """
        data = self.parse_msg(msg)
        if not data['border']:
            return irouter.process(self,msg)

        if data['AS'] == self.AS:
            # border router of same as,
            # exchange BGP info
            self.my_as_brouters.append((data['ID'],data['src_ip']))
            # get LSA stuff and process like
            # irouter
            lsa_stuff = msg.split("OPTIONS")[0]
            lsa_stuff = lsa_stuff.strip()

            if data['injected']:
                irouter.process(self,lsa_stuff,data['ignore_networks'])
            else:
                irouter.process(self,lsa_stuff)
        else:
            # brouter of Different AS
            # Don't process lsa stuff
            if not self.other_as_brouters.has_key(data['AS']):
                self.other_as_brouters[data['AS']] = []

            if not (data['ID'],data['src_ip']) in self.other_as_brouters[data['AS']]:
                self.other_as_brouters[data['AS']].append((data['ID'],data['src_ip']))

            # also add a BGP path:
            # check if AS is peer/customer/provider,
            # add {Dest (=AS): [(path=[AS], brouter_id)]}
            AS = data['AS']

            networks = data['networks']
            if data['injected']:
                ignore_nets = data['injected_networks']
                networks = [net for net in set(networks).difference(set(ignore_nets))]

            self.networks_in_as[AS] = networks

            if AS in self.peers:
                if not self.paths_from_peers.has_key(AS):
                    self.paths_from_peers[AS] = []

                self.paths_from_peers[AS].append(([AS],data['ID']))

            if AS in self.customers:
                if not self.paths_from_customers.has_key(AS):
                    self.paths_from_customers[AS] = []

                self.paths_from_customers[AS].append(([AS],data['ID']))

            if AS in self.providers:
                if not self.paths_from_providers.has_key(AS):
                    self.paths_from_providers[AS] = []

                self.paths_from_providers[AS].append(([AS],data['ID']))

    def fwd_lsa(self, msg):
        if not "OPTIONS" in msg:
            msg = msg +" OPTIONS "+self.AS
        self.send(msg)

    def do_lsa(self):
        self.bid += 1
        for ip in self.addrs:
            net = ip[0]
            host= ip[1]

            dst = (net,'99')
            networks = ' '.join(self.nets)

            msg = str(ip).replace(' ','')+' '+str(dst).replace(' ','')+' LSA '+ \
            self.ID+' '+str(self.bid)+' NETWKS '+networks

            msg = msg + " OPTIONS BORDER "+ self.AS

            self.send(msg)

    def run(self,i):
        irouter.run(self,i)


if __name__ == "__main__":
    r = brouter(sys.argv)
    for i in range(40):
        if i == 4:
            print r.customers
            print r.providers
            r.do_bgpa()
        r.run(i)

