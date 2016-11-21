#coding=utf-8
import os
import pickle
import codecs
import sys
import xlrd
import xlwt
import re
import operator

import random
import cairo
import pycha.scatter
import pycha.bar
import jlink_gen_code as jlinkgc

#FIXME: MODIFY MAX Q
#max_q = 3100

time_soc_dataset=[];
time_count_name=[];
time_count_valset=[];

input_f=sys.argv[1];
input_dir=input_f[:input_f.rfind('/')]
print input_dir
f=open(input_f, 'r');
lines=f.readlines();

def RepresentsInt(s):
    try:
        int(s)
        return True
    except ValueError:
        return False

def get_target_val(line, split):
    cmd = '''echo "%s" | awk -F '%s' '{print $2}'  ''' % (line, split)
    ret = os.popen(cmd).readlines()[0].strip().split(",")[0];
    #print ret;
    return ret;

########## jlink_show_done_record 2437 ##########: ocv: 4211, cur: 9042, t: 512, size: 30 bvbat: 4137, vbat:(4096,4034)(4096 4043)
record_start=0;
top_rec=[];
cur_rec={};
sum_q=0;#mean vbat 3.45v
real_sum_q=0; #3.2v?
stop_sumq=0;
real_rec_num=0;
g_customer="customer"
g_vendor="vendor"
g_max_q = 3000;
l_idx=0;
for cur_line in lines:
    if l_idx == 1:
        g_customer = cur_line.strip();
    if l_idx == 2:
        g_vendor = cur_line.strip();
    if l_idx == 3:
        g_max_q = int(cur_line.strip());
    l_idx = l_idx + 1;
    if cur_line.find('jlink_show_done_record') != -1:
        print cur_line
        record_start=1;
        cur_rec["ocv"] = int(get_target_val(cur_line, "ocv:"));
        cur_rec["cur"] = int(get_target_val(cur_line, "cur:"));
        cur_rec["time"] = int(get_target_val(cur_line, "t:"));
        cur_rec["size"] = int(get_target_val(cur_line, "size:"));
        cur_rec["bvbat"] = int(get_target_val(cur_line, "bvbat:"));
        cur_rec["dis_q"] = cur_rec["time"]*cur_rec["cur"]/3600;
        if cur_rec["time"] > 13:
            real_sum_q = real_sum_q + cur_rec["dis_q"];
            real_rec_num = real_rec_num + 1;

        continue;
    if record_start == 1:
        cur_vbat = cur_line.split(",");
        cur_rec["vbats"]=cur_vbat;
        record_start = 2;
        continue;
    if record_start == 2:
        cur_mvbat = cur_line.split(",");
        cur_rec["mvbat"]=cur_mvbat;

        record_start = 3;
        if stop_sumq != 1:
            sum_q = sum_q + cur_rec["dis_q"];
            for vidx in range(len(cur_mvbat)):
                if RepresentsInt(cur_mvbat[vidx]):
                    if int(cur_mvbat[vidx]) < 3400:
                        print "!!!!!!!!!!!!!!!!!!!!!!!!! :stop"
                        stop_sumq=1;
                        sum_q = sum_q - cur_rec["dis_q"]*(len(cur_mvbat)-vidx)/len(cur_mvbat);
                        break;
                    
    print sum_q;
    if record_start == 3:
        print cur_rec
        top_rec.append(cur_rec);
        cur_rec={};
        record_start = -1;

print sum_q
print len(top_rec)
print real_rec_num;
print g_customer
print g_vendor
print g_max_q


def jlink_print_ocv_file():
    global sum_q;
    real_max_q = sum_q;#10mah

    cur_sums_q = top_rec[0]["dis_q"]
    out_data_sets=[];
    cur_dict={};
    cur_dict["ocv"] = top_rec[0]["ocv"];
    cur_dict["soc"] = 0;
    cur_dict["r"] = int((top_rec[1]["ocv"] - int(top_rec[0]["vbats"][top_rec[0]["size"] - 1]))*10000/top_rec[0]["cur"]);
    out_data_sets.append(cur_dict);
    print cur_dict
    for idx in range(1,77):
        cur_dict={};
        if idx < len(top_rec) :
            r = (top_rec[idx]["ocv"] - int(top_rec[idx-1]["vbats"][top_rec[idx-1]["size"] - 1]))*10000/top_rec[idx-1]["cur"]
            dq = top_rec[idx]["dis_q"];
            
            cur_dict["ocv"] = top_rec[idx]["ocv"];
            cur_dict["soc"] = (cur_sums_q*1000/real_max_q + 5)/10;
            cur_dict["r"] = r

            cur_sums_q = cur_sums_q + dq;
            print cur_sums_q, real_max_q
        else:
            cur_dict["ocv"] = 3218;
            cur_dict["soc"] = 100;
            cur_dict["r"] = 170;
        print cur_dict
        out_data_sets.append(cur_dict);
    
    jlinkgc.write_out_mtk_header(input_dir, g_customer, g_vendor, g_max_q, out_data_sets)
    jlinkgc.write_out_mtk_dtsi(input_dir,  g_customer, g_vendor, g_max_q, out_data_sets)
    jlinkgc.write_out_sprd_dtsi(input_dir, g_customer, g_vendor, g_max_q, out_data_sets)

jlink_print_ocv_file();

