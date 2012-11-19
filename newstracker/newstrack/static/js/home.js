function follow_topic(topic_id, u_id) {
  var post_follow_topic = {'t_id': topic_id, 'u_id': u_id};
  $.ajax({
    url: '/follow_topic/',
    type: 'post',
    dataType: 'json',
    data: JSON.stringify(post_follow_topic),
    success: function (follow_success) {
      if (follow_success) {
        //TODO: 位置移动。。。
        $('#topic-' + topic_id.toString() + '-' + u_id.toString()).addClass("unfollow-topic").removeClass("follow-topic").text("<i class="icon-remove"></i>取消关注")
      }
    }
  });
  return false;
}

function unfollow_topic(topic_id, u_id) {
  var post_unfollow_topic = {'t_id': topic_id, 'u_id': u_id};
  $.ajax({
    url: '/unfollow_topic/',
    type: 'post',
    dataType: 'json',
    data: JSON.stringify(post_unfollow_topic),
    success: function (unfollow_success) {
      if (unfollow_success) {
        //TODO: 位置移动。。。
        $('#topic-' + topic_id.toString() + '-' + u_id.toString()).addClass("follow_topic").removeClass("unfollow_topic").text("<i class="icon-heart"></i>关注")
      }
    }
  });
  return false;
}

function show_more_topics(start_idx, count, exclude_user) {
	// alert('show_more_topics:\nstart_idx:' + start_idx.toString() + '\ncount:' + count.toString() + '\nexclude_user:' + exclude_user.toString())
    var post_more_topics = {'start_idx': start_idx, 'count': count, 'exclude_user': exclude_user}
    $.ajax({
	    url: '/show_more_topics/',
	    type: 'post',
	    dataType: 'json',
	    data: JSON.stringify(post_more_topics),
	    success: function (more_topics) {
	      if (more_topics) {
	        $('#other-topic-list').append(more_topics)
	        $('.more-topic').attr('id', 'more-topic-' + (start_idx + count).toString())
	      }else{
	        $('.more-topic').text('no more data available').attr('href', 'javascript:void(0)')
	      }
	    }
    });
  return false;
}

$(document).ready(function () {
	
	$(".topic-operation").click(function (e) {
		if (!e.target) {
		    return;
		}
		e.preventDefault();
		t_id = parseInt(e.target.id.split("-")[1], 10);
		u_id = parseInt(e.target.id.split("-")[2], 10);
		if(!u_id) {
		    alert('请先登录');
		    return;
		}
		if(e.target.className.indexOf("follow-topic") != -1){
		    follow_topic(t_id, u_id);
		}else if(e.target.className.indexOf("unfollow-topic") != -1){
			unfollow_topic(t_id, u_id);
		}
	});
   
   $(".more-topic").click(function (e) {
	if (!e.target) {
	    return;
	}
	e.preventDefault();
	start_idx = parseInt(e.target.id.split("-")[2], 10);
	count = 5;
	exclude_user = true;
	show_more_topics(start_idx, count, exclude_user);
   });
        
});

