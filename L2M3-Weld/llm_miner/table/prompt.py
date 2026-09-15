# Source XML-to-Markdown examples, including merged rows and column headers.
CONVERT2MD = """Convert the following source XML table faithfully to a Markdown table.
Keep its label, caption, units, specimen labels, footnotes and every row, including empty cells.
Never infer an absent unit. If the table has no textual content, return exactly Empty content followed by <END>.
Repeat merged-cell labels only where the source span explicitly applies. Do not summarize or extract selected values.
Return the caption and Markdown without code fences, followed by the literal terminator <END>.
Example from DOI 10.1016/j.corsci.2025.112940, Table 3. Values are source data, not defaults.
Do not repair scientifically unusual source entries: preserve Flux and the reported gas mixture under their original column.

Input:
<table-wrap id="tbl1" orientation="portrait" position="float">
<label>1</label>
<caption>
<title>Knoevenagel Condensation Reaction of Butyl Cyanoacetate with Substrates Catalyzed by PCNs-100 and -101</title>
</caption>
<oasis:table colsep="0" rowsep="0">
<oasis:tgroup cols="1">
<oasis:colspec colname="col1"></oasis:colspec>
<oasis:tbody>
<oasis:row>
<oasis:entry>
<graphic id="fx1" orientation="portrait" position="anchor" xlink:href="ic-2010-01935f_0011.tif"></graphic>
</oasis:entry>
</oasis:row>
</oasis:tbody>
</oasis:tgroup>
</oasis:table>
</table-wrap>
MD table:
Empty content
<END>


Input: <table id="tbl0015" colsep="0" rowsep="0" frame="topbot"> <label>Table 3</label><caption id="cap0085"> <simple-para id="sp0090" view="all">Welding parameters of different welding processes.</simple-para></caption><alt-text id="at0085" role="short">Table 3</alt-text><tgroup cols="7"> <colspec colnum="1" colname="col1"/><colspec colnum="2" colname="col2"/><colspec colnum="3" colname="col3"/><colspec colnum="4" colname="col4"/><colspec colnum="5" colname="col5"/><colspec colnum="6" colname="col6"/><colspec colnum="7" colname="col7"/><thead> <row rowsep="1"> <entry/><entry>Bead sequence</entry><entry>Current<br/></entry><entry>Voltage<br/></entry><entry>Welding Speed(cm/min)</entry><entry>Heat Input（kJ/cm)</entry><entry>Shielding gas flow(L/min)</entry></row></thead><tbody> <row> <entry morerows="1" role="rowhead">SAW</entry><entry>Inside pass</entry><entry align="char" char=".">560</entry><entry align="char" char=".">34</entry><entry align="char" char=".">125</entry><entry align="char" char=".">9.14</entry><entry role="rowgroup" morerows="1">Flux</entry></row><row> <entry align="char" char=".">Outside pass</entry><entry align="char" char=".">600</entry><entry align="char" char=".">37</entry><entry align="char" char=".">125</entry><entry>10.7</entry></row><row> <entry morerows="2" role="rowhead">TIG</entry><entry>backing weld</entry><entry align="char" char=".">180</entry><entry align="char" char="." role="rowgroup" morerows="2">21</entry><entry align="char" char=".">35</entry><entry align="char" char=".">6.48</entry><entry role="rowgroup" morerows="2">80 %Ar+ 20 % CO<inf loc="post">2</inf></entry></row><row> <entry>Intermediate weld</entry><entry align="char" char=".">130</entry><entry align="char" char=".">40</entry><entry>4.10</entry></row><row> <entry>cosmetic weld</entry><entry align="char" char=".">100</entry><entry align="char" char=".">24</entry><entry>5.25</entry></row></tbody></tgroup></table>
MD table:
Table 3. Welding parameters of different welding processes.
|  | Bead sequence | Current | Voltage | Welding Speed(cm/min) | Heat Input（kJ/cm) | Shielding gas flow(L/min) |
| --- | --- | --- | --- | --- | --- | --- |
| SAW | Inside pass | 560 | 34 | 125 | 9.14 | Flux |
| SAW | Outside pass | 600 | 37 | 125 | 10.7 | Flux |
| TIG | backing weld | 180 | 21 | 35 | 6.48 | 80 %Ar+ 20 % CO2 |
| TIG | Intermediate weld | 130 | 21 | 40 | 4.10 | 80 %Ar+ 20 % CO2 |
| TIG | cosmetic weld | 100 | 21 | 24 | 5.25 | 80 %Ar+ 20 % CO2 |
<END>

Example from DOI 10.1016/j.msea.2016.09.103, Table 4 (namespace prefixes omitted).
Combine the two header levels so each hydrogen condition retains its impact-energy unit.
Preserve the uncertainty values and do not confuse charging duration with test temperature.

Input:
<table id="t0020" colsep="0" rowsep="0" frame="top">
  <label>Table 4</label>
  <caption id="cap0075">
    <simple-para id="sp0075" view="all">Results of impact energy test on charged and uncharged E7018 and E7010-G weld metals.</simple-para>
  </caption>
  <alt-text id="at0075" role="short">Table 4</alt-text>
  <tgroup cols="3">
    <colspec colnum="1" colname="col1"/>
    <colspec colnum="2" colname="col2"/>
    <colspec colnum="3" colname="col3"/>
    <thead>
      <row>
        <entry><bold>Electrode</bold></entry>
        <entry rowsep="1" namest="col2" nameend="col3"><bold>Impact energy (Joule)</bold></entry>
      </row>
      <row rowsep="1">
        <entry/>
        <entry><bold>No hydrogen precharging</bold></entry>
        <entry><bold>14<hsp sp="0.25"/>h hydrogen Prechargin</bold>g</entry>
      </row>
    </thead>
    <tbody>
      <row>
        <entry role="rowhead">E7010-G (WM)</entry>
        <entry>93±16</entry>
        <entry>93±20</entry>
      </row>
      <row rowsep="1">
        <entry role="rowhead">E7018 (WM)</entry>
        <entry>185±6</entry>
        <entry>180±11</entry>
      </row>
    </tbody>
  </tgroup>
</table>
MD table:
Table 4. Results of impact energy test on charged and uncharged E7018 and E7010-G weld metals.
| Electrode | Impact energy (Joule) / No hydrogen precharging | Impact energy (Joule) / 14 h hydrogen Precharging |
| --- | --- | --- |
| E7010-G (WM) | 93±16 | 93±20 |
| E7018 (WM) | 185±6 | 180±11 |
<END>

Input: {paragraph}
"""


FT_CONVERT = """Convert the following source XML table faithfully to a Markdown table.
Keep its label, caption, units, specimen labels, footnotes and every row, including empty cells.
Never infer an absent unit. If the table has no textual content, return exactly Empty content followed by <END>.
Repeat merged-cell labels only where the source span explicitly applies. Do not summarize or extract selected values.
Return the caption and Markdown without code fences, followed by the literal terminator <END>.
Input: {paragraph}
"""


FT_HUMAN = "{paragraph}"
