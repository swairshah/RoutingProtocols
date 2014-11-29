from time import sleep
import os

class controller:
    def __init__(self):
        self.readers = []
        for i in os.listdir('host'):
            f = open('host/'+i,'r')
            self.readers.append(f)

    def send(self, msg, net):
        msg = msg+'\n'
        f = open('net/NET'+net,'a')
        f.write(msg)
        f.close()

    def read(self):
        for r in self.readers:
            msg = r.readline().strip()
            if msg != '':
                self.process(msg)

    def process(self, msg):
        """
        parse messages read from outXX files
        example msg: 
        src         dst            nid bid       networks 
        ('08','05') ('08','99') LSA 11 25 NETWKS 09 08 12
        """
        src_dst, rest = msg.split("LSA")

        nid_bid = rest.strip().split("NETWKS")[0]
        nid, bid = nid_bid.strip().split(' ')

        dst = src_dst.strip().split(' ')[1]
        dst_net = dst.strip("()").split(',')[0].strip("'")

        #print "received: nid "+ nid +" bid: "+ bid+" dst: "+ dst_net

        self.send(msg,dst_net)

if __name__ == "__main__":
    c = controller()
    for i in range(50):
        c.read()
        sleep(1)

