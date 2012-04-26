<%inherit file="base.html"/>
<%block name="title">Schema Editor</%block>

<form action="${url("/schemas/%s" % class_)}" method="post">

<table class="rey-table rey-rectable">
  <tr>
    <th>Internal Name</th>
    <td>${class_}</td>
  </tr>
  <tr>
    <th>Description</th>
    <td>
      <input type="text"
             size="30"
             name="description"
             id="description"
             value="${meta.get('description', '')}"/>
    </td>
  </tr>
  <tr>
    <th>Metaclass</th>
    <td>
      <select name="metaclass" id="metaclass">
        <%
            opts = (('simple', 'Simple Object'),
                    ('lines', 'Lines of Text'))
        %>
        %for k, v in opts:
            %if meta.get('metaclass') == k:
            <option value="${k}" selected="selected">${v}</option>
            %else:
            <option value="${k}">${v}</option>
            %endif
        %endfor
      </select>
    </td>
  </tr>
  <tr>
    <th>Key Field</th>
    <td>
    <select name="key_field" id="key_field">
    %for spec in schema:
    %if spec[3].strip() != '':
    <option value="${spec[2]}">${spec[3]}</option>
    %else:
    <option value="${spec[2]}">${spec[2]}</option>
    %endif
    %endfor
    </select>
    </td>
  </tr>
  <tr>
    <th>Default Sort</th>
    <td>
    <select name="default_sort" id="default_sort">
    %for spec in schema:
    %if spec[3].strip() != '':
    <option value="${spec[2]}">${spec[3]}</option>
    %else:
    <option value="${spec[2]}">${spec[2]}</option>
    %endif
    %endfor
    </select>
    </td>
  </tr>
</table>

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
            ("DO", "Document"),
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
