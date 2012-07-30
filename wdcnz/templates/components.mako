
<%def name="tweet_list(title='Tweets')">

<table class="table table-bordered">
    <thead>
        <tr>
            <th><h2>${title}</h2></th>
        </tr>
    </thead>
    <tbody>
        % for tweet in tweets:
            <tr>
                <td>
                    <h4>
                        <a href="/users/${tweet["user_name"]}">${tweet["user_name"]}</a>&nbsp;
                        <small>${util.timestamp_desc(tweet["timestamp"])}</small>
                        %if user["user_name"] == tweet["user_name"]:
                        <form class="pull-right" action="/tweets/deleted" method="post">
                            <input type="hidden" class="" placeholder="" name="tweet_id" value="${tweet['tweet_id']}"></input>
                            <button class="btn btn-danger" href="#">
                                <i class="icon-trash icon-white"></i>
                                    Delete
                            </button>
                        </form>
                        %endif
                    </h4>
                    <p>${tweet["body"]}</p>
                </td>
            </tr>
        % endfor
    </tbody>
</table>

</%def>

<%def name="user_list(users, title)">
<table class="table table-bordered">
    <thead>
        <tr>
            <th><h2>${title}</h2></th>
        </tr>
    </thead>
    <tbody>
        % for user in users:
            <tr>
                <td>
                    <h4>
                        <a href="/users/${user["user_name"]}" title="${user.get("real_name")}">${user.get("real_name", user["user_name"])}</a>&nbsp;
                        <small>${user["user_name"]}</small>
                    </h4>
                </td>
            </tr>
        % endfor
    </tbody>
</table>
</%def>
