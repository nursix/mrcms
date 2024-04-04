# Database upgrade script
#
# MRCMS Template Version 1.5.1
#
# Execute in web2py folder before code upgrade like:
# python web2py.py -S eden -M -R applications/eden/modules/templates/MRCMS/upgrade/prep-1.5.2.py
#
import os

sql = '''ALTER TABLE "act_activity" RENAME COLUMN "time" TO "time_info"'''
db.executesql(sql);
db.commit();
