import sys
import os.path
from time import sleep,localtime,strftime,time
from graph import Graph

class irouter:
    def __init__(self,args = None):

        if args is None:
            # just for test
            return

        self.ID, self.addrs = self.parse_args(args)

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

    def parse_args(self,args):
        """
        takes the whole argument string, (sys.argv)
        returns id,list_of_(nn,hh)
        """
        if len(args) < 3:
            raise Exception("check the arguments you passed!")

        ID = args[1]
        ip_addrs = list()

        addr_num = len(args[2:])
        if addr_num % 2 != 0:
            raise Exception("seems like nn,hh pairs are not complete!")

        for i in xrange(1,addr_num/2+1):
            nn = args[i*2]
            hh = args[i*2+1]
            ip_addrs.append(tuple([nn,hh]))

        return ID,ip_addrs

    def send(self,msg):
        f = file(self.file,'a')
        f.write(msg+'\n')
        f.close()

    def read(self):
        for r in self.readers:
            msg = r.readline().strip()
            if msg != '':
                self.process(msg)

    def process_brouter(self, msg):
        pass

    def parse_msg(self, msg):
        """ Example:
        parse_msg((08,05) (08,99) LSA 11 25 NETWKS 09 08 12 OPTIONS BORDER 02)
        returns:
        ret = {
            'networks': ['09','08','12'],
            'ID'      : '11',
            'bid'     : '25',
            'src_ip'  : ('08','05'),
            'dst_ip'  : ('08','99'),
            'bcast'   : true,
            'AS'      : '02', # optional
            'border'  : True  # optional
        }
        """
        ret = {} 
        ret['border'] = False
        ret['injected'] = False
        if "LSA" in msg:
            if "OPTIONS" in msg:
                lsa_stuff, brouter_stuff = msg.split("OPTIONS") 
                msg = lsa_stuff.strip()
                if "BORDER" in brouter_stuff:
                    ret['border'] = True
                    AS = brouter_stuff.strip().split(' ')[1]
                    ret['AS'] = AS
                else:
                    AS = lsa_stuff.strip()
                    ret['AS'] = AS

                if "INJECTED" in brouter_stuff:
                    ret['injected'] = True
                    inj_nets = brouter_stuff.split('INJECTED')[1]
                    inj_nets = inj_nets.strip().split(' ')
                    ret['injected_networks'] = inj_nets

        rest,networks = msg.split("NETWKS")
        ret['networks'] = networks.strip().split(' ')

        src,dst,lsa_str, nid, bid = rest.strip().split(' ')

        ret['ID'] = nid.strip()
        ret['bid'] = bid.strip()
        
        src_dst, tmp = rest.split("LSA")
        src, dst = src_dst.strip().split(' ')

        dst_net = dst.strip('()').split(',')[0].strip("'")
        dst_host = dst.strip('()').split(',')[1].strip("'")

        src_net = src.strip('()').split(',')[0].strip("'")
        src_host = src.strip('()').split(',')[1].strip("'")

        ret['src_ip'] = (src_net, src_host)
        ret['dst_ip'] = (dst_net, dst_host)

        return ret
        
    def process(self,msg, ignore_nets = []):
        """
        src     dst        nid bid       networks 
        (08,05) (08,99) LSA 11 25 NETWKS 09 08 12
        """
        rest, networks = msg.split("NETWKS")
        networks = networks.strip().split(' ')

        networks = [net for net in set(networks).difference(set(ignore_nets))]
        # tmp1 contains LSA string, so ignore
        src, dst, tmp1, nid, bid = rest.strip().split(' ')

        if "LSA" in msg and nid != self.ID:

            # if msg is from a border router remove part 
            # after "OPTIONS" from the msg pass the extra
            # part to another method which'll be 
            # implemented in brouter class
            if "OPTIONS" in msg:
                lsa_msg, rest = msg.split("OPTIONS")
                self.process_brouter(msg)
                msg = lsa_msg.strip()
            
            if self.old_bids.has_key(nid):
                #check if values corresp. to
                # nid contains this bid
                if bid != self.old_bids[nid]:
                    self.old_bids[nid] = bid
            # make a new k:v in dict old_bids
            # as nid:[bid]
            else:
                self.old_bids[nid] = bid
                self.old_bid_timers[nid] = time()

                self.g.add_node(nid, networks)

                src_dst, rest = msg.split("LSA")
                rest = " LSA "+rest.strip()
                old_src, old_dst = src_dst.strip().split(' ')
                old_net = old_dst.strip('()').split(',')[0].strip("'")
                # forward message 
                for ip in self.addrs:
                    net = ip[0]
                    host = ip[1]
                    #print "net: "+net+" old_net "+old_net+" "+str(net == old_net)
                    if net != old_net:
                        new_dst = (net,'99')
                        fwd_msg = old_src+" "+str(new_dst).replace(' ','')+rest
                        self.fwd_lsa(fwd_msg)

    def fwd_lsa(self, msg):
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

            self.send(msg)

    def mk_routing_table(self):
        """
        routing table entries look like:
        dest next_hop time_stamp
        03   02       01:41:05 2014-11-26
        """
        
        # check old_bid_timers, if node's last
        # bid was 30 seconds before current time,
        # delete node from graph.
        current_time = time()
        for node,last_time in self.old_bid_timers.iteritems():
            if current_time - last_time > 30.0:
                print self.ID,' removing node:', node, 'timediff: ', (current_time-last_time) 
                self.g.remove_node(node)

        f = open(self.routing,'a')
        for n in self.g.nodes:
            shortest_path = self.g.shortest_path(self.ID, n)
            print self.ID, n, " path ", str(shortest_path)

            if shortest_path == None:
                next_hop = "--"
            elif len(shortest_path) > 1:
                next_hop = shortest_path[1]
            else:
                next_hop = self.ID

            #time_stamp = strftime("%H:%M:%S %Y-%m-%d", time.localtime())
            time_stamp = strftime("%H:%M:%S", localtime())
            route = n+" "+next_hop+" "+time_stamp
            f.write(route+"\n")

        f.close()

    def run(self,i):
        self.read()
        #print self.ID+" :bids "+str(self.old_bids)
        #if i%10 == 0: 
        if i%10 == 0: 
            self.do_lsa()
        if i%15 == 0:
            pass
        if i%30 == 0:
            #TODO: check for dead nodes
            self.mk_routing_table()
            print "graph for "+self.ID+" : "+ str(self.g.graph)
            pass
        sleep(1)


if __name__ == "__main__":
    r = irouter(sys.argv)
    for i in range(60):
        r.run(i)

