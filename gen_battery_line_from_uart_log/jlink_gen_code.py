#coding=utf-8
import os
import pickle
import codecs
import sys
import xlrd
from openpyxl import load_workbook
import xlsxwriter
import re
import operator
import random
import cairo
import pycha.scatter
import pycha.bar

time_soc_dataset=[];
time_count_name=[];
time_count_valset=[];
time_ocv_dataset=[];
soc_r_dataset=[];

soc_for_sprd=1;
nums_for_mtk=77;


#bat_data_sets format:
#   struct is list.
#       member is a dict: "soc", "ocv", "r"



####################################   header ###################################
def write_out_mtk_header(o_path, g_customer, g_vendor, g_max_q, bat_data_sets):
    print o_path, g_customer, g_vendor, g_max_q
    #print bat_data_sets;

    out_ocv="//start define\nBATTERY_PROFILE_STRUC lk_py_%s_%s_ocv_%dmah[] =\n{\n\t{0, %d},\n" % (g_customer, g_vendor, g_max_q,bat_data_sets[0]["ocv"]);
    out_r="R_PROFILE_STRUC lk_py_%s_%s_r_%dmah[] =\n{\n\t{%d, %d},\n" % (g_customer, g_vendor, g_max_q, bat_data_sets[0]["r"], bat_data_sets[0]["ocv"]);
    for idx in range(len(bat_data_sets)):
        out_ocv="%s\t{%d, %d},\n" % (out_ocv, bat_data_sets[idx]["soc"], bat_data_sets[idx]["ocv"])
        out_r="%s\t{%d, %d},\n" % (out_r, bat_data_sets[idx]["r"], bat_data_sets[idx]["ocv"])

    out_ocv="%s};\n" % out_ocv;
    out_r="%s};\n" % out_r;

    out_file=o_path + "/jlink_%s_%s_%dmah.h" % (g_customer, g_vendor, g_max_q)
    genf=open(out_file, 'w+');
    genf.write(out_ocv);
    genf.write(out_r);
    genf.close();

####################################   dtsi ###################################
def write_out_mtk_dtsi(o_path, g_customer, g_vendor, g_max_q, bat_data_sets):
    print o_path, g_customer, g_vendor, g_max_q
    #print bat_data_sets;
    max_q = g_max_q

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


    out_ocv = "%sbattery_profile_t2_num = <%d>;\nbattery_profile_t2 = <0 %d\n" % (dtsi_start, len(bat_data_sets), bat_data_sets[0]["ocv"])
    out_r = "r_profile_t2_num = <%d >;\nr_profile_t2 = <0 %d\n" % (len(bat_data_sets), bat_data_sets[0]["ocv"])

    for idx in range(len(bat_data_sets)):
        out_ocv="%s%d %d\n" % (out_ocv, bat_data_sets[idx]["soc"], bat_data_sets[idx]["ocv"])
        out_r="%s%d %d\n" % (out_r, bat_data_sets[idx]["r"], bat_data_sets[idx]["ocv"])

    out_file=o_path + "/jlink_%s_%s_%dmah.dtsi" % (g_customer, g_vendor, g_max_q)
    genf=open(out_file, 'w+');
    genf.write(out_ocv);
    genf.write(out_r);
    genf.close();

####################################   dtsi ###################################
def write_out_sprd_dtsi(o_path, g_customer, g_vendor, g_max_q, bat_data_sets):
    print o_path, g_customer, g_vendor, g_max_q
    #print bat_data_sets;
    max_q = g_max_q

#	ocv-tab-vol = <4337 4273 4217 4163 4111 4067 4008 3973 3935 3884 3849 3826 3807 3792 3779 3764 3745 3721 3691 3682 3400>;
#	ocv-tab-cap = <100  95   90   85   80   75   70   65   60   55   50   45   40   35   30   25   20   15   10   5    0>;
    dtsi_start='''/ {
	//start
		/* battery: %s %s %dmah */
		sprd_battery_x: sprd_battery_x {
		compatible = "sprd,sprd-battery-cust-x";
''' % (g_customer, g_vendor,g_max_q)
   
    out_ocv ="\t\tocv-tab-vol = <%d " % (bat_data_sets[0]["ocv"])
    out_cap = "\t\tocv-tab-cap = <100 ";
    out_r_ocv = "\t\trint-tab-ocv = <%d " % (bat_data_sets[0]["ocv"])
    out_r_rint = "\t\trint-tab-rint = <0 ";

    for idx in range(1, len(bat_data_sets)):
        out_ocv="%s%d " % (out_ocv, bat_data_sets[idx]["ocv"])
        out_cap="%s%d " % (out_cap, 100-bat_data_sets[idx]["soc"])
        out_r_ocv="%s%d " % (out_r_ocv, bat_data_sets[idx]["ocv"])
        out_r_rint="%s%d " % (out_r_rint, bat_data_sets[idx]["r"])

    out_head = "%s\t\tocv-tab-size = <%d>;\n\t\trint-tab-size = <%d>;\n" % (dtsi_start, len(bat_data_sets), len(bat_data_sets))
    out_ocv = "%s>;\n" % out_ocv
    out_cap = "%s>;\n" % out_cap        
    out_r_ocv = "%s>;\n" % out_r_ocv
    out_r_rint = "%s>;\n" % out_r_rint

    out_file=o_path + "/jlink_%s_%s_%dmah_sprd.dtsi" % (g_customer, g_vendor, g_max_q)
    genf=open(out_file, 'w+');
    genf.write(out_head);
    genf.write(out_ocv);
    genf.write(out_cap);
    genf.write(out_r_ocv);
    genf.write(out_r_rint);
    genf.close();

