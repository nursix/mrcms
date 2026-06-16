# Database upgrade script
#
# MRCMS Template Version 1.8.5 => 1.8.6
#
# Run after code upgrade like:
# edenctl run applications/eden/modules/templates/MRCMS/upgrade/1.8.5-1.8.6.py
#
import sys
import datetime

from core import S3Duplicate

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
stable = s3db.org_sector
ntable = s3db.dvr_need
ttable = s3db.dvr_response_theme

# Paths
IMPORT_XSLT_FOLDER = os.path.join(request.folder, "static", "formats", "s3csv")
TEMPLATE_FOLDER = os.path.join(request.folder, "modules", "templates", "MRCMS")

settings.base.debug = True

# -----------------------------------------------------------------------------
# Deploy new need categories
#
if not failed:
    info("Deploy new need categories")

    resource = s3db.resource("dvr_need")

    # Only import relevant CMS posts, do not update existing ones
    def deduplicate(item):
        name = item.data.get("name")
        if name in ("Kinderschutz",
                    "BAMF-Bescheid",
                    "Asylverfahren Klage",
                    ):
            S3Duplicate(noupdate=True)(item)
        else:
            item.skip = True
    resource.configure(deduplicate = deduplicate)

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
# Update response themes
#
if not failed:
    info("Update response themes...")

    query = (stable.name == "Asylverfahrensberatung") & \
            (stable.deleted == False)
    row = db(query).select(stable.id, limitby=(0, 1)).first()
    sector_id = row.id if row else None

    query = (ntable.name == "BAMF-Bescheid") & \
            (ntable.deleted == False)
    row = db(query).select(stable.id, limitby=(0, 1)).first()
    need_id = row.id if row else None

    if sector_id and need_id:
        query = (ttable.name == "Dublin 1 Bescheid erklären") & \
                (ttable.deleted == False)
        updated = db(query).update(name = "Bescheid erhalten (Dublin)",
                                   need_id = need_id,
                                   sector_id = sector_id,
                                   modified_on = ttable.modified_on,
                                   modified_by = ttable.modified_by,
                                   )
        infoln("done (%s themes updated)" % updated)
    else:
        infoln("failed")
        failed = True

if not failed:
    info("Update theme labels...")

    change = {"Dublin 2 Anwalt: Vermittlung": "Dublin 1 Anwalt: Vermittlung",
              "Dublin 3 Anwalt: Dokumente übermittelt": "Dublin 2 Anwalt: Dokumente übermittelt",
              "Dublin 3.1. Anwalt: Kontaktaufnahme": "Dublin 3 Anwalt: Kontaktaufnahme",
              }

    updated = 0
    for old, new in change.items():
        updated += db(ttable.name==old).update(name=new,
                                               modified_on = ttable.modified_on,
                                               modified_by = ttable.modified_by,
                                               )
    infoln("done (%s themes updated)" % updated)

if not failed:
    info("Deploy new themes...")

    # Only import new themes, do not update existing ones
    resource = s3db.resource("dvr_response_theme")
    resource.configure(deduplicate = S3Duplicate(primary = ("name",),
                                                 secondary = ("organisation_id",
                                                              "sector_id",
                                                              "need_id",
                                                              ),
                                                 noupdate = True,
                                                 ))

    # File and stylesheet paths
    stylesheet = os.path.join(IMPORT_XSLT_FOLDER, "dvr", "response_theme.xsl")
    filename = os.path.join(TEMPLATE_FOLDER, "dvr_response_theme.csv")

    # Import, capture errors
    result = None
    try:
        with open(filename, "r") as File:
            result = resource.import_xml(File, source_type="csv", stylesheet=stylesheet)
    except Exception as e:
        error = sys.exc_info()[1] or "unknown error"
    else:
        error = resource.error

    # Fail on any error
    if error:
        infoln("...failed")
        infoln(error)
        failed = True
    elif result:
        infoln("...done (%s new themes imported)" % len(result.created))

# -----------------------------------------------------------------------------
# Update vulnerability types
#
if not failed:
    info("Deploy new vulnerability types...")

    # Only import new types, do not update existing ones
    resource = s3db.resource("dvr_vulnerability_type")
    resource.configure(deduplicate = S3Duplicate(primary = ("name",),
                                                 secondary = ("code",),
                                                 noupdate = True,
                                                 ))

    # File and stylesheet paths
    stylesheet = os.path.join(IMPORT_XSLT_FOLDER, "dvr", "vulnerability_type.xsl")
    filename = os.path.join(TEMPLATE_FOLDER, "dvr_vulnerability_type.csv")

    # Import, capture errors
    result = None
    try:
        with open(filename, "r") as File:
            result = resource.import_xml(File, source_type="csv", stylesheet=stylesheet)
    except Exception as e:
        error = sys.exc_info()[1] or "unknown error"
    else:
        error = resource.error

    # Fail on any error
    if error:
        infoln("...failed")
        infoln(error)
        failed = True
    elif result:
        infoln("...done (%s new types imported)" % len(result.created))

# -----------------------------------------------------------------------------
# Update response types
#
if not failed:
    info("Deploy new response types...")

    # Only import new types, do not update existing ones
    resource = s3db.resource("dvr_response_type")
    resource.configure(deduplicate = S3Duplicate(primary = ("name",),
                                                 secondary = ("parent",),
                                                 noupdate = True,
                                                 ))

    # File and stylesheet paths
    stylesheet = os.path.join(IMPORT_XSLT_FOLDER, "dvr", "response_type.xsl")
    filename = os.path.join(TEMPLATE_FOLDER, "dvr_response_type.csv")

    # Import, capture errors
    result = None
    try:
        with open(filename, "r") as File:
            result = resource.import_xml(File, source_type="csv", stylesheet=stylesheet)
    except Exception as e:
        error = sys.exc_info()[1] or "unknown error"
    else:
        error = resource.error

    # Fail on any error
    if error:
        infoln("...failed")
        infoln(error)
        failed = True
    elif result:
        infoln("...done (%s new types imported)" % len(result.created))

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
