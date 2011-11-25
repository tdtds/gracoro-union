# -*- coding: utf-8; -*-
#
# watch.rb : gracoro-union worker process watching twitter apecified hashtag.
#
# Copyright (C) 2011 by TADA Tadashi <t@tdtds.jp>
#
require 'tweetstream'
require './lib/connect'
require './lib/tweet'
require './lib/person'
require 'erb'

TweetStream.configure do |config|
	config.consumer_key = ENV['TWITTER_CONSUMER_KEY']
	config.consumer_secret = ENV['TWITTER_CONSUMER_SECRET']
	config.oauth_token = ENV['TWITTER_OAUTH_TOKEN']
	config.oauth_token_secret = ENV['TWITTER_OAUTH_TOKEN_SECRET']
	config.auth_method = :oauth
end

search_string = '#gracoro_union'

begin
	TweetStream::Client::new.on_error {|message|
		puts message
	}.track( search_string ) do |status|
		begin
			next if /@\S/ === status.text # skipping replies included.
			person = Person.where( name: status.user[:screen_name] ).first ||
				Person::create( name: status.user[:screen_name], count: 0 )
			person.count += 1
			person.icon = status.user[:profile_image_url]
			person.save
			Tweet::create(
				_id: status.id,
				name: status.user[:screen_name],
				icon: status.user[:profile_image_url],
				text: status.text ).save
			p status.user[:screen_name]
		rescue
			p "ERROR: #$!"
		end
	end
rescue
	p "ERROR: #$!"
	sleep 10
	retry
end

# [:truncated, :text, :id_str, :retweeted, :in_reply_to_status_id_str, :in_reply_to_user_id, :in_reply_to_user_id_str, :entities, :source, :created_at, :contributors, :place, :geo, :favorited, :coordinates, :user, :in_reply_to_status_id, :id, :retweet_count, :in_reply_to_screen_name]
