# Copyright (c) 2026, Your Organization
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime, today


class DiscussionThread(Document):
	def validate(self):
		self.set_created_by()
		self.update_last_post()

	def set_created_by(self):
		"""Set created by if new document."""
		if self.is_new() and not self.created_by:
			self.created_by = frappe.session.user
			self.creation_date = today()

	def update_last_post(self):
		"""Update last post timestamp."""
		if self.posts:
			last_post = max(self.posts, key=lambda p: p.posted_on or frappe.utils.now_datetime())
			self.last_post_on = last_post.posted_on

	def add_post(self, content):
		"""Add a new post to the discussion."""
		if not content:
			frappe.throw(_("Post content cannot be empty."))
		
		self.append("posts", {
			"post_content": content,
			"posted_by": frappe.session.user,
			"posted_on": now_datetime()
		})
		self.save()

	def pin_thread(self):
		"""Pin the discussion thread."""
		self.db_set("is_pinned", 1)

	def unpin_thread(self):
		"""Unpin the discussion thread."""
		self.db_set("is_pinned", 0)

	def mark_resolved(self):
		"""Mark the discussion as resolved."""
		self.db_set("is_resolved", 1)

	def mark_unresolved(self):
		"""Mark the discussion as unresolved."""
		self.db_set("is_resolved", 0)


class DiscussionPost(Document):
	def before_save(self):
		"""Track edit count for edited posts."""
		if not self.is_new():
			self.is_edited = 1
			self.edit_count = (self.edit_count or 0) + 1
