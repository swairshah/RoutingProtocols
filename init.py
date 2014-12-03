#!/usr/bin/python2
for i in xrange(100):
    if i<10:
        s = '0'+str(i)
    else:
        s = str(i)

    f = open('net/NET'+s,'w')
    f.write('')
    f.close()


    f = open('rt/rt'+s,'w')
    f.write('dst_net next_hop timestamp\n')
    f.close()
    

    if i < 15:
        f = open('host/out'+s,'w')
        f.write('')
        f.close()

        s1 = 'ID'+str(i)
        f = open('host/out'+s1,'w')
        f.write('')
        f.close()

        f = open('rt/rt'+s1,'w')
        f.write('dst_net next_hop timestamp\n')
        f.close()

