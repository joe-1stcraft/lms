import frappe


def execute():
    frappe.reload_doc("lms", "doctype", "lms_question")
