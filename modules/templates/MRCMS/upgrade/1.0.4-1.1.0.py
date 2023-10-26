# Database upgrade script
#
# MRCMS Template Version 1.0.4 => 1.1.0
#
# Execute in web2py folder after code upgrade like:
# python web2py.py -S eden -M -R applications/eden/modules/templates/MRCMS/upgrade/1.0.4-1.1.0.py
#
import sys

#from core import S3Duplicate

# Override auth (disables all permission checks)
auth.override = True

# Initialize failed-flag
failed = False

# Info
def info(msg):
    sys.stderr.write("%s" % msg)
    sys.stderr.flush()
def infoln(msg):
    sys.stderr.write("%s\n" % msg)
    sys.stderr.flush()

# Load models for tables
rtable = s3db.s3_permission
ntable = s3db.dvr_need

# Paths
IMPORT_XSLT_FOLDER = os.path.join(request.folder, "static", "formats", "s3csv")
TEMPLATE_FOLDER = os.path.join(request.folder, "modules", "templates", "MRCMS")

# -----------------------------------------------------------------------------
# Rename need categories
#
if not failed:
    info("Update need categories")

    terminology = {"Registration": "Registrierung",
                   "Asylum Application": "Allgemeine Infos zum Asylverfahren",
                   "Shelter": "Unterbringungssituation",
                   "Family Reunification": "Familieneinheit",
                   "Food": "Versorgung/Angebote in der Einrichtung",
                   "Cash": "Taschengeld",
                   "Mail": "Post",
                   "Health": "Gesundheitsbedarfe",
                   "Education": "Arbeit und Bildung",
                   "Protection": "Besonderer Schutzbedarf",
                   }
    updated = 0
    for original, new in terminology.items():
        updated += db(ntable.name==original).update(name=new)
        info(".")
    infoln("...done (%s categories updated)" % updated)

# -----------------------------------------------------------------------------
# Deploy new need categories
#
if not failed:
    info("Deploy new need categories")

    resource = s3db.resource("dvr_need")

    # File and stylesheet paths
    stylesheet = os.path.join(IMPORT_XSLT_FOLDER, "dvr", "need.xsl")
    filename = os.path.join(TEMPLATE_FOLDER, "dvr_need.csv")

    # Import, capture errors
    try:
        with open(filename, "r") as File:
            resource.import_xml(File, source_type="csv", stylesheet=stylesheet)
    except Exception as e:
        error = sys.exc_info()[1] or "unknown error"
    else:
        error = resource.error

    # Fail on any error
    if error:
        infoln("...failed")
        infoln(error)
        failed = True
    else:
        infoln("...done")

# -----------------------------------------------------------------------------
# Deploy case activity statuses
#
if not failed:
    info("Deploy case activity statuses")

    resource = s3db.resource("dvr_case_activity_status")

    # File and stylesheet paths
    stylesheet = os.path.join(IMPORT_XSLT_FOLDER, "dvr", "case_activity_status.xsl")
    filename = os.path.join(TEMPLATE_FOLDER, "dvr_case_activity_status.csv")

    # Import, capture errors
    try:
        with open(filename, "r") as File:
            resource.import_xml(File, source_type="csv", stylesheet=stylesheet)
    except Exception as e:
        error = sys.exc_info()[1] or "unknown error"
    else:
        error = resource.error

    # Fail on any error
    if error:
        infoln("...failed")
        infoln(error)
        failed = True
    else:
        infoln("...done")

# -----------------------------------------------------------------------------
# Deploy case activity update types
if not failed:
    info("Deploy case activity update types")

    resource = s3db.resource("dvr_case_activity_update_type")

    # File and stylesheet paths
    stylesheet = os.path.join(IMPORT_XSLT_FOLDER, "dvr", "case_activity_update_type.xsl")
    filename = os.path.join(TEMPLATE_FOLDER, "dvr_case_activity_update_type.csv")

    # Import, capture errors
    try:
        with open(filename, "r") as File:
            resource.import_xml(File, source_type="csv", stylesheet=stylesheet)
    except Exception as e:
        error = sys.exc_info()[1] or "unknown error"
    else:
        error = resource.error

    # Fail on any error
    if error:
        infoln("...failed")
        infoln(error)
        failed = True
    else:
        infoln("...done")

# -----------------------------------------------------------------------------
# Deploy vulnerability types
if not failed:
    info("Deploy vulnerability types")

    resource = s3db.resource("dvr_vulnerability_type")

    # File and stylesheet paths
    stylesheet = os.path.join(IMPORT_XSLT_FOLDER, "dvr", "vulnerability_type.xsl")
    filename = os.path.join(TEMPLATE_FOLDER, "dvr_vulnerability_type.csv")

    # Import, capture errors
    try:
        with open(filename, "r") as File:
            resource.import_xml(File, source_type="csv", stylesheet=stylesheet)
    except Exception as e:
        error = sys.exc_info()[1] or "unknown error"
    else:
        error = resource.error

    # Fail on any error
    if error:
        infoln("...failed")
        infoln(error)
        failed = True
    else:
        infoln("...done")

# -----------------------------------------------------------------------------
# Deploy response types
#
if not failed:
    info("Deploy response types")

    resource = s3db.resource("dvr_response_type")

    # File and stylesheet paths
    stylesheet = os.path.join(IMPORT_XSLT_FOLDER, "dvr", "response_type.xsl")
    filename = os.path.join(TEMPLATE_FOLDER, "dvr_response_type.csv")

    # Import, capture errors
    try:
        with open(filename, "r") as File:
            resource.import_xml(File, source_type="csv", stylesheet=stylesheet)
    except Exception as e:
        error = sys.exc_info()[1] or "unknown error"
    else:
        error = resource.error

    # Fail on any error
    if error:
        infoln("...failed")
        infoln(error)
        failed = True
    else:
        infoln("...done")

# -----------------------------------------------------------------------------
# Deploy response action statuses
#
if not failed:
    info("Deploy response statuses")

    resource = s3db.resource("dvr_response_status")

    # File and stylesheet paths
    stylesheet = os.path.join(IMPORT_XSLT_FOLDER, "dvr", "response_status.xsl")
    filename = os.path.join(TEMPLATE_FOLDER, "dvr_response_status.csv")

    # Import, capture errors
    try:
        with open(filename, "r") as File:
            resource.import_xml(File, source_type="csv", stylesheet=stylesheet)
    except Exception as e:
        error = sys.exc_info()[1] or "unknown error"
    else:
        error = resource.error

    # Fail on any error
    if error:
        infoln("...failed")
        infoln(error)
        failed = True
    else:
        infoln("...done")

# -----------------------------------------------------------------------------
# Deploy response themes
#
if not failed:
    info("Deploy response themes")

    resource = s3db.resource("dvr_response_theme")

    # File and stylesheet paths
    stylesheet = os.path.join(IMPORT_XSLT_FOLDER, "dvr", "response_theme.xsl")
    filename = os.path.join(TEMPLATE_FOLDER, "dvr_response_theme.csv")

    # Import, capture errors
    try:
        with open(filename, "r") as File:
            resource.import_xml(File, source_type="csv", stylesheet=stylesheet)
    except Exception as e:
        error = sys.exc_info()[1] or "unknown error"
    else:
        error = resource.error

    # Fail on any error
    if error:
        infoln("...failed")
        infoln(error)
        failed = True
    else:
        infoln("...done")

# -----------------------------------------------------------------------------
# Upgrade user roles
#
if not failed:
    info("Upgrade user roles")

    # Delete invalid rules
    deleted = 0
    query = (rtable.tablename == "dvr_response_type_case_activity")
    deleted +=db(query).delete()
    info("...%s invalid rules removed" % deleted)

    # Re-import correct rules
    bi = s3base.BulkImporter()
    filename = os.path.join(TEMPLATE_FOLDER, "auth_roles.csv")

    try:
        error = bi.import_roles(filename)
    except Exception as e:
        error = sys.exc_info()[1] or "unknown error"
    if error:
        infoln("...failed")
        infoln(error)
        failed = True
    else:
        infoln("...done")

# -----------------------------------------------------------------------------
# Finishing up
#
if failed:
    db.rollback()
    infoln("UPGRADE FAILED - Action rolled back.")
else:
    db.commit()
    infoln("UPGRADE SUCCESSFUL.")

# END =========================================================================
