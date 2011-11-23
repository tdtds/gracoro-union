# -*- coding: utf-8; -*-
#
# Copyright (C) 2011 by TADA Tadashi <t@tdtds.jp>
#
require 'mongoid'

class Person
	include Mongoid::Document

	field :name, type: String
	field :icon, type: String
	field :count, type: Integer
end

