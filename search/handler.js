'use strict';

var AWS = require("aws-sdk");
var url = require('url');
var domain = 'photo-archive';
const itemsPerPage = 100;

module.exports.handle = async event => {
  const total = await getTotal();
  let where = '';
  const body = JSON.parse(event.body || event);
  const params = url.parse('?' + body, true).query;
  let page = 1;
  if (typeof params.page != 'undefined') {
    page = params.page;
  }
  // KEYWORD MATCHING
  where = '';
  if (typeof params.q != 'undefined' && params.q != '') {
    const keywords = params.q;
    where += ' (';
    where += 'caption LIKE "%' + keywords + '%" OR caption LIKE "%' + keywords.toLowerCase() + '%"';
    where += ' OR headline LIKE "%' + keywords + '%" OR headline LIKE "%' + keywords.toLowerCase() + '%"';
    where += ' OR tags LIKE "%' + keywords + '%" OR tags LIKE "%' + keywords.toLowerCase() + '%"';
    where += ' OR itemName() LIKE "%' + keywords + '%" OR itemName() LIKE "%' + keywords.toLowerCase() + '%"';
    where += ')';
  }
  // SORT
  if (where != '') {
    where += ' AND ';
  }
  where += ' created_at IS NOT NULL ORDER BY created_at DESC';
  // FORMAT WHERE CLAUSE
  if (where != '') {
    where = ' WHERE ' + where;
  }
  const selectors = '*';
  const searchStatement = 'SELECT ' + selectors + ' FROM `' + domain + '` ' + where + ' limit ' + itemsPerPage;
  const offset = (page - 1) * itemsPerPage;
  let nextToken = '';
  if (offset > 0) {
    nextToken = await getNextTokenForOffset(where, offset);
  }
  const searchResults = await query(searchStatement, nextToken);
  const responseObject = {
    total: total,
    results: searchResults
  };
  if (typeof params.page == 'undefined' || params.page == '' || params.page == 1) {
    const countStatement = 'SELECT COUNT(*) FROM `' + domain + '` ' + where;
    const countResults = await query(countStatement, '');
    responseObject['count'] = parseCountResults(countResults);
  }
  return {
    statusCode: 200,
    body: JSON.stringify(responseObject)
  };
};

async function getTotal() {
  const statement = 'select COUNT(*) from `' + domain + '`';
  const results = await query(statement, '');
  return parseCountResults(results);
}

function parseCountResults(results) {
  for (const attribute of results.Items[0].Attributes) {
    if (attribute.Name == 'Count') {
      return attribute.Value;
    }
  }
  return 0;
}

function query(expression, nextToken) {
  return new Promise(function(resolve, reject) {
    var simpledb = new AWS.SimpleDB({apiVersion: '2009-04-15'});
    const params = {
      SelectExpression: expression,
      ConsistentRead: true,
      NextToken: nextToken
    };
    simpledb.select(params, function (err, data) {
      if (err) resolve(err); // an error occurred
      else     resolve(data); // successful response
    });
  });
}

async function getNextTokenForOffset(where, offset) {
  const statement = 'SELECT COUNT(*) FROM `' + domain + '` ' + where + ' LIMIT ' + offset;
  const results = await query(statement, '');
  return results.NextToken;
}