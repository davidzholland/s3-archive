'use strict';

var AWS = require("aws-sdk");


module.exports.handle = async event => {
  let where = '';
  const body = JSON.parse(event.body || event);
  if (typeof body.q != 'undefined') {
    const keywords = body.q;
    where = ' WHERE caption LIKE "%' + keywords + '%" OR caption LIKE "%' + keywords.toLowerCase() + '%"';
    where += ' OR headline LIKE "%' + keywords + '%" OR headline LIKE "%' + keywords.toLowerCase() + '%"';
    where += ' OR tags LIKE "%' + keywords + '%" OR tags LIKE "%' + keywords.toLowerCase() + '%"';
  }
  const statement = 'select * from `photo-archive` ' + where + ' limit 5';
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