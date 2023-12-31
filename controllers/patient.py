"""
    Patient Tracking
"""

module = request.controller

if not settings.has_module(module):
    raise HTTP(404, body="Module disabled: %s" % module)

# -----------------------------------------------------------------------------
def index():
    "Module's Home Page"

    module_name = settings.modules[module].get("name_nice")
    response.title = module_name
    return dict(module_name=module_name)

# -----------------------------------------------------------------------------
def person():
    """ Person controller for PersonSelector """

    def prep(r):
        if r.representation != "s3json":
            # Do not serve other representations here
            return False
        else:
            current.xml.show_ids = True
        return True
    s3.prep = prep

    return crud_controller("pr", "person")

# -----------------------------------------------------------------------------
def patient():
    """ RESTful CRUD controller """

    tablename = "patient_patient"

    # Load Models
    s3db.table("patient_patient")

    s3db.configure(tablename,
                   create_next = URL(args=["[id]", "relative"]))
    # Pre-process
    def prep(r):
        if r.id:
            s3db.configure("patient_relative",
                           create_next = URL(args=[str(r.id), "home"]))
        return True
    s3.prep = prep

    # Post-process
    def postp(r, output):
        # No Delete-button in list view
        s3_action_buttons(r, deletable=False)
        return output
    s3.postp = postp

    tabs = [(T("Basic Details"), None),
            (T("Accompanying Relative"), "relative"),
            (T("Home"), "home")]

    rheader = lambda r: patient_rheader(r, tabs=tabs)
    return crud_controller(rheader=rheader)

# -----------------------------------------------------------------------------
def patient_rheader(r, tabs=[]):
    """ Resource Page Header """

    if r.representation == "html":

        if r.record is None:
            # List or Create form: rheader makes no sense here
            return None

        table = db.patient_patient

        rheader_tabs = s3_rheader_tabs(r, tabs)

        patient = r.record
        if patient.person_id:
            name = s3_fullname(patient.person_id)
        else:
            name = None

        if patient.country:
            country = table.country.represent(patient.country)
        else:
            country = None

        if patient.hospital_id:
            hospital = table.hospital_id.represent(patient.hospital_id)
        else:
            hospital = None

        rheader = DIV(TABLE(
            TR(
                TH("%s: " % T("Patient")),
                name,
                TH("%s: " % COUNTRY),
                country),
            TR(
                TH(),
                TH(),
                TH("%s: " % T("Hospital")),
                hospital,
                )
        ), rheader_tabs)

        return rheader

    return None

# END =========================================================================
