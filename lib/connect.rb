# -*- coding: utf-8; -*-
#
# Copyright (C) 2011 by TADA Tadashi <t@tdtds.jp>
#
require 'mongoid'

raise StandardError::new( 'no TWITTER_CONSUMER_KEY' ) unless ENV['TWITTER_CONSUMER_KEY']
raise StandardError::new( 'no TWITTER_CONSUMER_SECRET' ) unless ENV['TWITTER_CONSUMER_SECRET']
raise StandardError::new( 'no TWITTER_OAUTH_TOKEN' ) unless ENV['TWITTER_OAUTH_TOKEN']
raise StandardError::new( 'no TWITTER_OAUTH_TOKEN_SECRET' ) unless ENV['TWITTER_OAUTH_TOKEN_SECRET']

Mongoid.configure do |conf|
	mongo_uri = ENV['MONGOLAB_URI']
	if mongo_uri
		uri = URI.parse( mongo_uri )
		conn = Mongo::Connection.from_uri( mongo_uri )
		conf.master = conn.db( uri.path.gsub( %r|^/|, '' ) )
	else
		conn = Mongo::Connection.new
		conf.master = conn.db( 'gracoro_union' )
	end
end
