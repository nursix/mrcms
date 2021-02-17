{{# These are messages which are translatable & can then be available to Static JavaScript}}
i18n={}
i18n.ac_widget_more_results='{{=T("Greater than 10 matches. Please refine search further")}}'
i18n.all='{{=T("All")}}'
i18n.ajax_wht='{{=T("We have tried")}}'
i18n.ajax_gvn='{{=T("times and it is still not working. We give in. Sorry.")}}'
i18n.ajax_500='{{=XML(T("An error occured, please %(reload)s the page.") % dict(reload = A(T("reload"), _href=URL(args=request.args, vars=request.get_vars))))}}'
i18n.ajax_dwn='{{=T("There was a problem, sorry, please try again later.")}}'
i18n.ajax_get='{{=T("getting")}}'
i18n.ajax_fmd='{{=T("form data")}}'
i18n.ajax_rtr='{{=T("retry")}}'
i18n.close_map='{{=T("Close map")}}'
i18n.delete_confirmation='{{=T("Are you sure you want to delete this record?")}}'
i18n.disable_with_message='{{=T("Working...")}}'
i18n.enter_value='{{=T("enter a value")}}'
i18n.hour='{{=T("Hour")}}'
i18n.input_number='{{=T("Please enter a number only")}}'
i18n.language='{{=s3.language}}'
i18n.minute='{{=T("Minute")}}'
i18n.no_match='{{=T("No match")}}'
i18n.no_matching_records='{{=T("No matching records found")}}'
i18n.unsaved_changes="{{=T("You have unsaved changes. Click Cancel now, then 'Save' to save them. Click OK now to discard them.")}}"
{{fb_pixel_id = settings.get_facebook_pixel_id()}}{{ga_id = settings.get_google_analytics_tracking_id()}}{{if fb_pixel_id or ga_id:}}
i18n.analytics='{{=T("Analytics")}}'
i18n.analytics_desc='{{=T("Cookies related to site visits, browser types, etc.")}}'
{{pass}}