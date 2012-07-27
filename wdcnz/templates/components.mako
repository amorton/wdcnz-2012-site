
<%def name="tweet_list()">
    % for tweet in tweets:
      <div class="tweet">
          <blockquote>
              <p>${tweet["body"]}</p>
              <small><a href="/users/${tweet["user_name"]}" title="${tweet.get("user_name")}">${tweet["user_name"]}</a></small>
          </blockquote>
      </div>
    % endfor
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
