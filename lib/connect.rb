# -*- coding: utf-8; -*-
#
require 'mongoid'

raise StandardError::new( 'no TWITTER_CONSUMER_KEY' ) unless ENV['TWITTER_CONSUMER_KEY']
raise StandardError::new( 'no TWITTER_CONSUMER_SECRET' ) unless ENV['TWITTER_CONSUMER_SECRET']
raise StandardError::new( 'no TWITTER_OAUTH_TOKEN' ) unless ENV['TWITTER_OAUTH_TOKEN']
raise StandardError::new( 'no TWITTER_OAUTH_TOKEN_SECRET' ) unless ENV['TWITTER_OAUTH_TOKEN_SECRET']

Mongoid.configure do |conf|
	if ENV['MONGOHQ_URL']
		uri = URI.parse(ENV['MONGOHQ_URL'])
		conn = Mongo::Connection.from_uri( ENV['MONGOHQ_URL'] )
		conf.master = conn.db( uri.path.gsub( %r|^/|, '' ) )
	else
		conn = Mongo::Connection.new
		conf.master = conn.db( 'gracoro_union' )
	end
end
