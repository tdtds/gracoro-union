# -*- coding: utf-8; -*-
#
require 'mongoid'

class Tweet
	include Mongoid::Document

	field :name, type: String
	field :text, type: String
end
