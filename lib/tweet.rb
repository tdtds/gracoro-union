# -*- coding: utf-8; -*-
#
# Copyright (C) 2011 by TADA Tadashi <t@tdtds.jp>
#
require 'mongoid'

class Tweet
	include Mongoid::Document

	field :name, type: String
	field :text, type: String
end
