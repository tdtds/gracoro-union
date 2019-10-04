# -*- coding: utf-8; -*-
#
# Copyright (C) 2011 by TADA Tadashi <t@tdtds.jp>
#
raise StandardError::new( 'no TWITTER_CONSUMER_KEY' ) unless ENV['TWITTER_CONSUMER_KEY']
raise StandardError::new( 'no TWITTER_CONSUMER_SECRET' ) unless ENV['TWITTER_CONSUMER_SECRET']
raise StandardError::new( 'no TWITTER_OAUTH_TOKEN' ) unless ENV['TWITTER_OAUTH_TOKEN']
raise StandardError::new( 'no TWITTER_OAUTH_TOKEN_SECRET' ) unless ENV['TWITTER_OAUTH_TOKEN_SECRET']

uri = ENV['MONGODB_URI'] || ENV['MONGOLAB_URI'] || 'mongodb://localhost:27017/gracoro_union'
Mongo::Logger.level = Logger::WARN
Mongoid::Config.load_configuration({
	clients:{
		default:{
			uri: uri,
			options:{retry_writes: false}
		}
	}
})
