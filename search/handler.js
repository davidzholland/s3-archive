'use strict';

var AWS = require("aws-sdk");
var url = require('url');


module.exports.handle = async event => {
  let where = '';
  const body = JSON.parse(event.body || event);
  const params = url.parse('?' + body, true).query;
  if (typeof params.q != 'undefined') {
    const keywords = params.q;
    where = ' WHERE caption LIKE "%' + keywords + '%" OR caption LIKE "%' + keywords.toLowerCase() + '%"';
    where += ' OR headline LIKE "%' + keywords + '%" OR headline LIKE "%' + keywords.toLowerCase() + '%"';
    where += ' OR tags LIKE "%' + keywords + '%" OR tags LIKE "%' + keywords.toLowerCase() + '%"';
    where += ' OR itemName() LIKE "%' + keywords + '%" OR itemName() LIKE "%' + keywords.toLowerCase() + '%"';
  }
  const statement = 'select * from `photo-archive` ' + where + ' limit 25';
  console.log('statement: ', statement);
  const results = await query(statement);
  return {
    statusCode: 200,
    body: JSON.stringify(results)
  };
};

function query(expression) {
  return new Promise(function(resolve, reject) {
    var simpledb = new AWS.SimpleDB({apiVersion: '2009-04-15'});
    const params = {
      SelectExpression: expression,
      ConsistentRead: true
    };
    simpledb.select(params, function (err, data) {
      if (err) resolve(err); // an error occurred
      else     resolve(data); // successful response
    });
  });
}