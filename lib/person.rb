# -*- coding: utf-8; -*-
#
require 'mongoid'

class Person
	include Mongoid::Document

	field :name, type: String
	field :count, type: Integer
end

