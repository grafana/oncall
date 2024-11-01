---
title: Phone calls and SMS notifications
menuTitle: Phone and SMS
description: Learn more about Phone calls and SMS notifications for Grafana OnCall.
weight: 100
keywords:
  - OnCall
  - Notifications
  - SMS
  - Phone
  - Rate Limits
canonical: https://grafana.com/docs/oncall/latest/manage/notify/phone-calls-sms/
aliases:
  - /docs/grafana-cloud/alerting-and-irm/oncall/manage/notify/phone-calls-sms/
  - /docs/grafana-cloud/alerting-and-irm/oncall/notify/phone-calls-sms/
  - ../../notify/phone-sms/ # /docs/oncall/<ONCALL_VERSION>/notify/phone-sms/
  - ../../notify/phone-calls-sms/ # /docs/oncall/<ONCALL_VERSION>/notify/phone-calls-sms/
refs:
  incoming-call-routing:
    - pattern: /docs/oncall/
      destination: /docs/oncall/<ONCALL_VERSION>/configure/live-call-routing/
    - pattern: /docs/grafana-cloud/
      destination: /docs/grafana-cloud/alerting-and-irm/oncall/configure/live-call-routing/
  mobile-app:
    - pattern: /docs/oncall/
      destination: /docs/oncall/<ONCALL_VERSION>/manage/mobile-app/
    - pattern: /docs/grafana-cloud/
      destination: /docs/grafana-cloud/alerting-and-irm/oncall/manage/mobile-app/
  grafana-oss-cloud-setup:
    - pattern: /docs/oncall/
      destination: /docs/oncall/<ONCALL_VERSION>/set-up/open-source/#grafana-oss-cloud-setup
    - pattern: /docs/grafana-cloud/
      destination: /docs/grafana-cloud/alerting-and-irm/oncall/set-up/open-source/#grafana-oss-cloud-setup
---

# Phone calls and SMS notifications

Grafana OnCall Cloud includes SMS and Phone notifications.

{{< admonition type="note" >}}
OSS users can use the [Grafana OSS-Cloud Setup](ref:grafana-oss-cloud-setup) as a relay or configure this notification type using other providers like Twilio.
{{< /admonition >}}

Please note, not all countries are supported. Grafana OnCall aligns with Twilio’s suggested list of supported countries.
For details, see [SMS/Voice support by country](#smsvoice-support-by-country).

## SMS notification behavior

OnCall reduces alert noise and distraction by bundling SMS notifications.
When multiple alert groups require notification within a short period, the first alert group triggers an immediate SMS.
A 2-minute "waiting period" follows, during which additional alerts are bundled. After this period, a single SMS with all alert information is sent.

Notifications are bundled based on their importance. Alerts from "default" and "important" notification policies are bundled separately.

### Example

If a user needs to be notified about 5 alert groups from 2 different integrations (3 from "Grafana Alerting" and 2 from "Health Check"),
they will receive an immediate notification for the first alert group and a bundled SMS for the remaining alerts after 2 minutes:

#### Example bundled notification

Grafana OnCall: Alert groups #101, #102, #103 and 1 more, from stack: TestOrg, integrations: GrafanaAlerting and 1 more.

## Route incoming calls to the on-call engineer

For guidance on configuring incoming call routing, refer to our [documentation](ref:incoming-call-routing), and [blog post](https://grafana.com/blog/2024/06/10/a-guide-to-grafana-oncall-sms-and-call-routing/)

## About phone call and SMS notifications

Please note the following about phone calls and SMS notifications:

### Additional costs for outgoing calls/SMS

There are no additional costs for outgoing calls or SMS notifications.

### Rate limits for Calls/SMS

There are no specific rate limits, but we reserve the right to stop sending SMS/calls in case of abnormal volume.

### Grafana OnCall phone numbers

To learn the phone number used by OnCall, make a test call from the “Phone Verification” tab.

### SMS/Voice support by country

The following is a list of countries currently supported by Grafana OnCall.

{{< admonition type="note" >}}
Be aware that due to limitations
in our telecom provider’s service, some numbers within supported countries may occasionally be flagged as “high-risk” when
verifying your phone number, thereby preventing you from being able to use that number to receive notifications.

Ensure that you test your notification rules to confirm that OnCall can reach you. For added reliability, consider backing
up phone calls and SMS notifications with additional methods, such as the [Mobile app](/docs/grafana-cloud/alerting-and-irm/irm/irm-mobile-app/push-notifications/).
{{< /admonition >}}

{{< collapse title="Europe" >}}

| Country                                              | SMS/Voice Support |
| ---------------------------------------------------- | ----------------- |
| Andorra (+376)                                       | ✅                |
| Albania (+355)                                       | ✅                |
| Austria (+43)                                        | ✅                |
| Aland Islands (+35818)                               | ✅                |
| Bosnia and Herzegovina (+387)                        | ✅                |
| Belgium (+32)                                        | ✅                |
| Bulgaria (+359)                                      | ✅                |
| Belarus (+375)                                       | ✅                |
| Switzerland (+41)                                    | ✅                |
| Czechia (+420)                                       | ✅                |
| Germany (+49)                                        | ✅                |
| Denmark (+45)                                        | ✅                |
| Estonia (+372)                                       | ✅                |
| Spain (+34)                                          | ✅                |
| Finland (+358)                                       | ✅                |
| Faroe Islands (+298)                                 | ❌                |
| France (+33)                                         | ✅                |
| United Kingdom (+44)                                 | ✅                |
| Guernsey (+441481)                                   | ✅                |
| Gibraltar (+350)                                     | ✅                |
| Greece (+30)                                         | ✅                |
| Croatia (+385)                                       | ✅                |
| Hungary (+36)                                        | ✅                |
| Ireland (+353)                                       | ✅                |
| Isle Of Man (+441624)                                | ✅                |
| Iceland (+354)                                       | ✅                |
| Italy (+39)                                          | ✅                |
| Jersey (+441534)                                     | ✅                |
| Liechtenstein (+423)                                 | ❌                |
| Lithuania (+370)                                     | ✅                |
| Luxembourg (+352)                                    | ✅                |
| Latvia (+371)                                        | ✅                |
| Monaco (+377)                                        | ❌                |
| Moldova (Republic of) (+373)                         | ✅                |
| Montenegro (+382)                                    | ✅                |
| North Macedonia (Republic of North Macedonia) (+389) | ✅                |
| Malta (+356)                                         | ✅                |
| Netherlands (+31)                                    | ✅                |
| Norway (+47)                                         | ✅                |
| Poland (+48)                                         | ✅                |
| Portugal (+351)                                      | ✅                |
| Romania (+40)                                        | ✅                |
| Serbia (+381)                                        | ✅                |
| Russian Federation (+7)                              | ✅                |
| Sweden (+46)                                         | ✅                |
| Slovenia (+386)                                      | ✅                |
| Svalbard and Jan Mayen Islands (+4779)               | ✅                |
| Slovakia (+421)                                      | ✅                |
| San Marino (+378)                                    | ❌                |
| Turkey (+90)                                         | ✅                |
| Ukraine (+380)                                       | ✅                |
| Holy See (Vatican City State) (+3906698)             | ❌                |
| Kosovo (+383)                                        | ❌                |
| Yugoslavia (+38)                                     | ✅                |

{{< /collapse >}}

{{< collapse title="Asia" >}}

| Country                                                   | SMS Support |
| --------------------------------------------------------- | ----------- |
| United Arab Emirates (+971)                               | ✅          |
| Afghanistan (+93)                                         | ❌          |
| Armenia (+374)                                            | ❌          |
| Azerbaijan (+994)                                         | ❌          |
| Bangladesh (+880)                                         | ❌          |
| Bahrain (+973)                                            | ✅          |
| Brunei Darussalam (+673)                                  | ✅          |
| Bhutan (+975)                                             | ✅          |
| Cocos (Keeling) Islands (+672)                            | ✅          |
| China (+86)                                               | ❌          |
| Christmas Island (+6189164)                               | ✅          |
| Cyprus (+357)                                             | ✅          |
| Georgia (+995)                                            | ✅          |
| Hong Kong (Special Administrative Region of China) (+852) | ✅          |
| Indonesia (+62)                                           | ✅          |
| Israel (+972)                                             | ✅          |
| India (+91)                                               | ✅          |
| British Indian Ocean Territory (+246)                     | ❌          |
| Iraq (+964)                                               | ❌          |
| Iran (Islamic Republic of) (+98)                          | ❌          |
| Jordan (+962)                                             | ❌          |
| Japan (+81)                                               | ✅          |
| Kyrgyzstan (+996)                                         | ❌          |
| Cambodia (+855)                                           | ❌          |
| Democratic People`s Republic of Korea (+850)              | ❌          |
| Republic of Korea (+82)                                   | ✅          |
| Kuwait (+965)                                             | ❌          |
| Kazakhstan (+7)                                           | ✅          |
| Lao People`s Democratic Republic (+856)                   | ❌          |
| Lebanon (+961)                                            | ❌          |
| Sri Lanka (+94)                                           | ❌          |
| Myanmar (+95)                                             | ❌          |
| Mongolia (+976)                                           | ❌          |
| Macau (Special Administrative Region of China) (+853)     | ✅          |
| Maldives (+960)                                           | ✅          |
| Malaysia (+60)                                            | ✅          |
| Nepal (+977)                                              | ❌          |
| Oman (+968)                                               | ❌          |
| Philippines (+63)                                         | ✅          |
| Pakistan (+92)                                            | ❌          |
| Palestinian Territory (Occupied) (+970)                   | ❌          |
| Qatar (+974)                                              | ✅          |
| Saudi Arabia (+966)                                       | ✅          |
| Singapore (+65)                                           | ✅          |
| Syrian Arab Republic (+963)                               | ❌          |
| Thailand (+66)                                            | ✅          |
| Tajikistan (+992)                                         | ❌          |
| Timor-Leste (East Timor) (+670)                           | ❌          |
| Turkmenistan (+993)                                       | ❌          |
| Taiwan (Province of China) (+886)                         | ✅          |
| Uzbekistan (+998)                                         | ❌          |
| Vietnam (+84)                                             | ❌          |
| Yemen (+967)                                              | ❌          |

{{< /collapse >}}

{{< collapse title="North America" >}}

| Country                                  | SMS Support |
| ---------------------------------------- | ----------- |
| Antigua and Barbuda (+1268)              | ❌          |
| Anguilla (+1264)                         | ❌          |
| Netherlands Antilles (+599)              | ✅          |
| Aruba (+297)                             | ✅          |
| Barbados (+1246)                         | ✅          |
| Saint Barthelemy (+590)                  | ✅          |
| Bermuda (+1441)                          | ✅          |
| Bonaire, Sint Eustatius And Saba (+5993) | ✅          |
| Bahamas (+1242)                          | ✅          |
| Belize (+501)                            | ❌          |
| Canada (+1)                              | ✅          |
| Costa Rica (+506)                        | ✅          |
| Cuba (+53)                               | ✅          |
| Dominica (+1767)                         | ❌          |
| Dominican Republic (+1809)               | ✅          |
| Grenada (+1473)                          | ❌          |
| Greenland (+299)                         | ❌          |
| Guadeloupe (+590)                        | ❌          |
| Guatemala (+502)                         | ✅          |
| Honduras (+504)                          | ❌          |
| Haiti (+509)                             | ✅          |
| Jamaica (+1876)                          | ✅          |
| Saint Kitts and Nevis (+1869)            | ❌          |
| Cayman Islands (+1345)                   | ✅          |
| Saint Lucia (+1758)                      | ❌          |
| Saint Martin French (+590)               | ❌          |
| Martinique (+596)                        | ❌          |
| Montserrat (+1664)                       | ❌          |
| Mexico (+52)                             | ✅          |
| Nicaragua (+505)                         | ✅          |
| Panama (+507)                            | ✅          |
| Saint Pierre and Miquelon (+508)         | ❌          |
| Puerto Rico (+1787)                      | ✅          |
| El Salvador (+503)                       | ❌          |
| Sint Maarten Dutch (+1721)               | ✅          |
| Turks and Caicos Islands (+1649)         | ❌          |
| Trinidad and Tobago (+1868)              | ✅          |
| United States (+1)                       | ✅          |
| Saint Vincent and the Grenadines (+1784) | ❌          |
| Virgin Islands British (+1284)           | ❌          |
| Virgin Islands US (+1340)                | ❌          |

{{< /collapse >}}

{{< collapse title="Africa" >}}

| Country                                 | SMS Support |
| --------------------------------------- | ----------- |
| Angola (+244)                           | ❌          |
| Burkina Faso (+226)                     | ✅          |
| Burundi (+257)                          | ❌          |
| Benin (+229)                            | ❌          |
| Botswana (+267)                         | ✅          |
| Democratic Republic of the Congo (+243) | ❌          |
| Central African Republic (+236)         | ❌          |
| Congo (+242)                            | ❌          |
| Cote d`Ivoire (+225)                    | ✅          |
| Cameroon (+237)                         | ❌          |
| Cape Verde (+238)                       | ✅          |
| Djibouti (+253)                         | ✅          |
| Algeria (+213)                          | ❌          |
| Egypt (+20)                             | ❌          |
| Western Sahara (+212)                   | ✅          |
| Eritrea (+291)                          | ❌          |
| Ethiopia (+251)                         | ❌          |
| Gabon (+241)                            | ❌          |
| Ghana (+233)                            | ❌          |
| Gambia (+220)                           | ❌          |
| Guinea (+224)                           | ❌          |
| Equatorial Guinea (+240)                | ❌          |
| Guinea-Bissau (+245)                    | ❌          |
| Kenya (+254)                            | ✅          |
| Comoros (+269)                          | ❌          |
| Liberia (+231)                          | ❌          |
| Lesotho (+266)                          | ❌          |
| Libyan Arab Jamahiriya (+218)           | ❌          |
| Morocco (+212)                          | ❌          |
| Madagascar (+261)                       | ❌          |
| Mali (+223)                             | ❌          |
| Mauritania (+222)                       | ✅          |
| Mauritius (+230)                        | ❌          |
| Malawi (+265)                           | ❌          |
| Mozambique (+258)                       | ✅          |
| Namibia (+264)                          | ✅          |
| Niger (+227)                            | ❌          |
| Nigeria (+234)                          | ✅          |
| Reunion (+262)                          | ❌          |
| Rwanda (+250)                           | ❌          |
| Seychelles (+248)                       | ❌          |
| Sudan (+249)                            | ❌          |
| Saint Helena (+290)                     | ✅          |
| Sierra Leone (+232)                     | ❌          |
| Senegal (+221)                          | ❌          |
| Somalia (+252)                          | ✅          |
| South Sudan (+211)                      | ❌          |
| Sao Tome and Principe (+239)            | ❌          |
| Swaziland (+268)                        | ✅          |
| Chad (+235)                             | ❌          |
| Togo (+228)                             | ✅          |
| Tunisia (+216)                          | ✅          |
| Tanzania (United Republic of) (+255)    | ✅          |
| Uganda (+256)                           | ✅          |
| Mayotte (+262269)                       | ✅          |
| South Africa (+27)                      | ✅          |
| Zambia (+260)                           | ❌          |
| Zimbabwe (+263)                         | ❌          |

{{< /collapse >}}

{{< collapse title="Antarctica" >}}

| Country                                             | SMS Support |
| --------------------------------------------------- | ----------- |
| Antarctica (+672)                                   | ✅          |
| Bouvet Island (+47)                                 | ✅          |
| South Georgia and The South Sandwich Islands (+500) | ✅          |
| Heard Island and McDonald Islands (+61)             | ✅          |
| French Southern Territories (+1)                    | ✅          |

{{< /collapse >}}

{{< collapse title="South America" >}}

| Country                            | SMS Support |
| ---------------------------------- | ----------- |
| Argentina (+54)                    | ✅          |
| Bolivia (+591)                     | ❌          |
| Brazil (+55)                       | ✅          |
| Chile (+56)                        | ✅          |
| Colombia (+57)                     | ✅          |
| Ecuador (+593)                     | ✅          |
| Falkland Islands (Malvinas) (+500) | ❌          |
| French Guiana (+594)               | ❌          |
| Guyana (+592)                      | ❌          |
| Peru (+51)                         | ✅          |
| Paraguay (+595)                    | ✅          |
| Suriname (+597)                    | ✅          |
| Uruguay (+598)                     | ✅          |
| Venezuela (+58)                    | ✅          |

{{< /collapse >}}

{{< collapse title="Oceania" >}}

| Country                                   | SMS Support |
| ----------------------------------------- | ----------- |
| American Samoa (+1684)                    | ❌          |
| Australia (+61)                           | ✅          |
| Cook Islands (+682)                       | ❌          |
| Curacao (+5999)                           | ✅          |
| Fiji (+679)                               | ✅          |
| Micronesia (Federated States of) (+691)   | ❌          |
| Guam (+1671)                              | ✅          |
| Kiribati (+686)                           | ❌          |
| Marshall Islands (+692)                   | ❌          |
| Northern Mariana Islands (+1670)          | ✅          |
| New Caledonia (+687)                      | ✅          |
| Norfolk Island (+672)                     | ✅          |
| Nauru (+674)                              | ❌          |
| Niue (+683)                               | ❌          |
| New Zealand (+64)                         | ✅          |
| French Polynesia (+689)                   | ✅          |
| Papua New Guinea (+675)                   | ❌          |
| Pitcairn (+64)                            | ✅          |
| Palau (+680)                              | ❌          |
| Solomon Islands (+677)                    | ❌          |
| Tokelau (+690)                            | ✅          |
| Tonga (+676)                              | ❌          |
| Tuvalu (+688)                             | ❌          |
| United States Minor Outlying Islands (+1) | ✅          |
| Vanuatu (+678)                            | ❌          |
| Wallis and Futuna Islands (+681)          | ❌          |
| Samoa (+685)                              | ❌          |

{{< /collapse >}}
