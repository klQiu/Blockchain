import csv

prosumer_datapath = '../data-emulator/prosumer/prosumer.csv'

with open('../data-emulator/prosumer/combined_prosumer.csv','w') as g:
    
    with open (prosumer_datapath) as f:
        line = f.readline()
        
        g.write(line)
        first_item =""
        second_item = 0
        count = 0

        line = f.readline()
        
        while line:
            if (count == 3):
                record = first_item + ","+str(second_item)
                g.write(record)
                g.write('\n')
                count =0
                first_item = ""
                second_item = 0
                
            else:
                split_line = line.split(",")
                if(first_item == ""):
                    first_item = split_line[0]
                
                second_item += float(split_line[1].strip('\n'))
                count +=1
                line = f.readline()

        record = first_item + ","+str(second_item)
        g.write(record)
        g.write('\n')

            

        

            



    
