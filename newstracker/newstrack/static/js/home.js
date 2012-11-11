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

function show_more() {
// TODO: impl
}

$(document).ready(function () {
  document.getElementById("all_topics").addEventListener("click", function (e) {
    if (!e.target) {
      return;
    }
    t_id = parseInt(e.target.id.split("_")[1], 10)
    u_id = parseInt(e.target.id.split("_")[2], 10) 
    
    switch (e.target.className) {
        case "follow_topic":
            if(!u_id) {
                alert('请先登录')
            }else{
              follow_topic(t_id, u_id);
            }
            break;
        case "unfollow_topic":
            if(!u_id) {
                alert('请先登录')
            }else{
              unfollow_topic(t_id, u_id);
            }
            break;
    }
  });
});

