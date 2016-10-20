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
                    if int(cur_mvbat[vidx]) < 3450:
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


def jlink_print_ocv_file(max_q, g_print_h, customer, vendor):
    global sum_q;
    real_max_q = sum_q;#10mah
    #print top_rec
    #cur_sums_q = top_rec[0]["cur"] * top_rec[0]["time"] / 36000;
    cur_sums_q = top_rec[0]["dis_q"]


    dtsi_start='''/ {
	//start
	bat_meter_cust_c: bat_meter_cust_c{
		compatible = "mediatek,bat_meter_cust_c";
		q_max_pos_50 = <%d >;
		q_max_pos_25 = <%d >;
		q_max_pos_0 = <%d >;
		q_max_neg_10 = <%d >;
		q_max_pos_50_h_current = <%d >;
		q_max_pos_25_h_current = <%d >;
		q_max_pos_0_h_current = <%d >;
		q_max_neg_10_h_current = <%d >;
		num_table = <1 >;
    ''' % (max_q,max_q,max_q,max_q,max_q,max_q,max_q,max_q)
    if g_print_h == 0:
        out_ocv = "%sbattery_profile_t2_num = <77>;\nbattery_profile_t2 = <0 %d\n" % (dtsi_start, top_rec[0]["ocv"])
        out_r = "r_profile_t2_num = <77 >;\nr_profile_t2 = <0 %d\n" % top_rec[0]["ocv"]
    else:
        out_ocv="//start define\nBATTERY_PROFILE_STRUC lk_py_%s_%s_ocv_%dmah[] =\n{\n{0, %d},\n" % (g_customer, g_vendor, g_max_q,top_rec[0]["ocv"]);
        out_r="R_PROFILE_STRUC lk_py_%s_%s_r_%dmah[] =\n{\n{0, %d},\n" % (g_customer, g_vendor, g_max_q,top_rec[0]["ocv"]);


    for idx in range(1,77):
        if idx < len(top_rec) :
            #print top_rec[idx-1]["size"] - 1

            r = (top_rec[idx]["ocv"] - int(top_rec[idx-1]["vbats"][top_rec[idx-1]["size"] - 1]))*10000/top_rec[idx-1]["cur"]
            dq = top_rec[idx]["dis_q"];
            #dq = top_rec[idx]["cur"] * top_rec[idx]["time"] / 36000
            #print top_rec[idx]["ocv"],int(top_rec[idx-1]["vbats"][top_rec[idx-1]["size"] - 1]), cur_sums_q, r, (cur_sums_q*1000/max_q + 5)/10
            #print (cur_sums_q*1000/max_q + 5)/10, (float(cur_sums_q)*100/float(max_q)), top_rec[idx]["ocv"], top_rec[idx]["dis_q"]

            if g_print_h == 0:
                out_ocv="%s%d %d\n" % (out_ocv, (cur_sums_q*1000/real_max_q + 5)/10, top_rec[idx]["ocv"])
            else:
                out_ocv="%s{%d, %d},\n" % (out_ocv, (cur_sums_q*1000/real_max_q + 5)/10, top_rec[idx]["ocv"])

            if g_print_h == 0:
                out_r="%s%d %d\n" % (out_r, r, top_rec[idx]["ocv"])
            else:
                out_r="%s{%d, %d},\n" % (out_r, r, top_rec[idx]["ocv"])
            cur_sums_q = cur_sums_q + dq;
            print cur_sums_q, real_max_q
        else:
            if g_print_h == 0:
                out_ocv="%s100 3212\n" % out_ocv;
            else:
                out_ocv="%s{100, 3212},\n" % out_ocv;

            if g_print_h == 0:
                out_r="%s180 3212\n" % out_r;
            else:
                out_r="%s{180, 3212},\n" % out_r;


    if g_print_h == 0:
        out_ocv = "%s>;\n" % out_ocv
        out_r = "%s>;\n};\n};" % out_r
    else:
        out_ocv="%s};\n" % out_ocv;
        out_r="%s};\n" % out_r;

    #print out_ocv
    #print out_r

    if g_print_h == 0:
        out_file=input_dir + "/lk_zcv_%s_%s_%dmah.dtsi" % (g_customer, g_vendor, g_max_q)
    else:
        out_file=input_dir + "/lk_zcv_%s_%s_%dmah.h" % (g_customer, g_vendor, g_max_q)
    genf=open(out_file, 'w+');
    genf.write(out_ocv);
    genf.write(out_r);
    genf.close();

def jlink_print_ocv_file_sprd(max_q, g_print_h, customer, vendor):
    global sum_q;
    real_max_q = sum_q;#10mah
    #print top_rec
    #cur_sums_q = top_rec[0]["cur"] * top_rec[0]["time"] / 36000;
    cur_sums_q = top_rec[0]["dis_q"]

#	ocv-tab-vol = <4337 4273 4217 4163 4111 4067 4008 3973 3935 3884 3849 3826 3807 3792 3779 3764 3745 3721 3691 3682 3400>;
#	ocv-tab-cap = <100  95   90   85   80   75   70   65   60   55   50   45   40   35   30   25   20   15   10   5    0>;
    dtsi_start='''/ {
	//start
		sprd_battery_x: sprd_battery_x {
		/* battery: %s %s %dmah real: %dmah*/
		compatible = "sprd,sprd-battery-cust-x";
		num_table = <1 >;
    ''' % (g_customer, g_vendor,g_max_q, real_max_q/10)
   
    out_ocv ="\tocv-tab-vol = <%d " % (top_rec[0]["ocv"])
    out_cap = "\tocv-tab-cap = <100 ";
    out_r_ocv = "\trint-tab-ocv = <%d " % (top_rec[0]["ocv"])
    out_r_rint = "\trint-tab-rint = <0 ";


    
    for idx in range(1,77):
        if idx < len(top_rec) :
            print idx
            #print top_rec[idx-1]["size"] - 1

            r = (top_rec[idx]["ocv"] - int(top_rec[idx-1]["vbats"][top_rec[idx-1]["size"] - 1]))*10000/top_rec[idx-1]["cur"]
            dq = top_rec[idx]["dis_q"];

            if g_print_h == 0:
                out_ocv="%s%d " % (out_ocv, top_rec[idx]["ocv"])
                out_cap="%s%d " % (out_cap, 100-(cur_sums_q*1000/real_max_q + 5)/10)

                out_r_ocv="%s%d " % (out_r_ocv, top_rec[idx]["ocv"])
                out_r_rint="%s%d " % (out_r_rint, r)

            else:
                out_ocv="%s{%d, %d},\n" % (out_ocv, (cur_sums_q*1000/real_max_q + 5)/10, top_rec[idx]["ocv"])

            cur_sums_q = cur_sums_q + dq;
            print cur_sums_q, real_max_q
            if cur_sums_q > real_max_q:
                break;
    print idx
    out_head = "%s\tocv-tab-size = <%d>;\n\trint-tab-size = <%d>;\n" % (dtsi_start, idx+2, idx+2)

    if g_print_h == 0:
        out_ocv = "%s>;\n" % out_ocv
        out_cap = "%s>;\n" % out_cap
        
        out_r_ocv = "%s>;\n" % out_r_ocv
        out_r_rint = "%s>;\n" % out_r_rint
    else:
        out_ocv="%s};\n" % out_ocv;
        out_r="%s};\n" % out_r;

    #print out_ocv
    #print out_r

    if g_print_h == 0:
        out_file=input_dir + "/lk_zcv_%s_%s_%dmah_sprd.dtsi" % (g_customer, g_vendor, g_max_q)
    else:
        out_file=input_dir + "/lk_zcv_%s_%s_%dmah.h" % (g_customer, g_vendor, g_max_q)
    genf=open(out_file, 'w+');
    genf.write(out_head);
    genf.write(out_ocv);
    genf.write(out_cap);
    genf.write(out_r_ocv);
    genf.write(out_r_rint);
    genf.close();


#jlink_print_ocv_file(3200, 0, "lingyun", "wls");
#jlink_print_ocv_file(3200, 1, "lingyun", "wls");
#jlink_print_ocv_file_sprd(3200, 0, "lingyun", "wls");

# we need customer in input line2, vendor in line3, max_q in line4.

jlink_print_ocv_file(3200, 0, "c", "v");
jlink_print_ocv_file(3200, 1, "c", "v");
jlink_print_ocv_file_sprd(3200, 0, "c", "v");
