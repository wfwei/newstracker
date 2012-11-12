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
        $('#topic_' + topic_id.toString() + '_' + u_id.toString()).addClass("unfollow_topic").removeClass("follow_topic").text("取消关注")
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
        $('#topic_' + topic_id.toString() + '_' + u_id.toString()).addClass("follow_topic").removeClass("unfollow_topic").text("关注")
      }
    }
  });
  return false;
}

function show_more_topics(start_idx, count, exclude_user) {
	//alert('show_more_topics:\nstart_idx:' + start_idx.toString() + '\ncount:' + count.toString() + '\nexclude_user:' + exclude_user.toString())
    var post_more_topics = {'start_idx': start_idx, 'count': count, 'exclude_user': exclude_user}
    $.ajax({
	    url: '/show_more_topics/',
	    type: 'post',
	    dataType: 'json',
	    data: JSON.stringify(post_more_topics),
	    success: function (more_topics) {
	      if (more_topics) {
	        $('#other_topics').append(more_topics)
	        $('.more_topic').attr('id', 'more_topic_' + (start_idx + count).toString())
	      }else{
	        $('.more_topic').text('no more data available').attr('href', 'javascript:void(0)')
	      }
	    }
    });
  return false;
}

$(document).ready(function () {
  document.getElementById("all_topics").addEventListener("click", function (e) {
    if (!e.target) {
      return;
    }
    switch (e.target.className) {
        case "follow_topic":
            e.preventDefault();
        	t_id = parseInt(e.target.id.split("_")[1], 10)
    		u_id = parseInt(e.target.id.split("_")[2], 10) 
            if(!u_id) {
                alert('请先登录')
            }else{
              follow_topic(t_id, u_id);
            }
            break;
        case "unfollow_topic":
            e.preventDefault();
        	t_id = parseInt(e.target.id.split("_")[1], 10)
    		u_id = parseInt(e.target.id.split("_")[2], 10)
            if(!u_id) {
                alert('请先登录')
            }else{
              unfollow_topic(t_id, u_id);
            }
            break;
        case "more_topic":
            e.preventDefault();
        	start_idx = parseInt(e.target.id.split("_")[2], 10)
        	count = 10
        	exclude_user = true
        	show_more_topics(start_idx, count, exclude_user);
            break;
    }
  });
});

