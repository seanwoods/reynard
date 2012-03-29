<%inherit file="base.html"/>
<%block name="title">Schema Editor</%block>

<form action="${url("/schemas/%s" % class_)}" method="post">
<table class="rey-table">
  <tr>
    <th>&nbsp;</th>
    <th>Field</th>
    <th>Description</th>
    <th>Type</th>
    <th>Extra</th>
  </tr>
  %for offset, urn, identifier, caption, datatype, extra in schema:
  <tr>
    <td>
      ${offset}
      <input type="hidden" name="order" value="${identifier}.${urn}"/>
    </td>
    <td>${identifier}</td>
    <td>
      <input type="text"
             name="${identifier}.caption"
             id="${identifier}.caption"
             size="25"
             value="${caption}"/>
    </td>
    <td>
      <%
        types = (
            ("T", "Text, Plain"),
            ("CS", "Choice, Single"),
            ("CM", "Choice, Multiple"),
            ("D", "Date"),
            ("DT", "Date and Time"),
            ("DO", "Database Document"),
            ("E", "E-Mail Address"),
            ("F", "File"),
            ("I", "Interval (Elapsed Time)"),
            ("P", "Pointer"),
            ("PM", "Pointer, Multiple"),
            ("PH", "Phone Number"),
            ("PW", "Password"),
            ("SL", "Slug"),
            ("ST", "State"),
            ("TI", "Time"),
            ("U", "Username"),
            ("W", "Web Site"),
            ("B", "Yes or No"),
            ("Z", "Zip Code")
        )
      %>
      <select name="${identifier}.datatype" id="${identifier}.datatype">
        %for abbrev, capt in types:
            %if abbrev == datatype:
            <option value="${abbrev}" selected="selected">${capt}</option>
            %else:
            <option value="${abbrev}">${capt}</option>
            %endif
        %endfor
      </select>
    </td>
    <td>
      <input type="text"
             name="${identifier}.extra"
             id="${identifier}.extra"
             size="25"
             value="${extra}"/>
    </td>
  </tr>
  %endfor
  <tr>
    <td colspan="5">
      <input type="submit" name="submit" value="Save Schema"/>
    </td>
  </tr>
</table>
</form>
