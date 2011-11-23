# -*- coding: utf-8; -*-
#
# webapp.rb : gracoro-union web application
#
# Copyright (C) 2011 by TADA Tadashi <t@tdtds.jp>
#

require 'rubygems'
require 'sinatra/base'
require 'haml'

require './lib/connect'
require './lib/person'

class GracoroUnion < Sinatra::Base
	set :haml, { format: :html5, escape_html: true }

	get '/' do
		@people = Person.all( sort: [[:count, :desc]], limit: 30 )
		haml :index
	end
end

GracoroUnion::run! if __FILE__ == $0
