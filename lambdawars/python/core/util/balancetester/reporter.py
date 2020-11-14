import filesystem
import os
from datetime import datetime
import srcmgr

htmltemplate = '''<!doctype html>
<html ng-app="app">
  <head>
    <title>Balance Report</title>
    <link rel="stylesheet" type="text/css" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.2/css/bootstrap.min.css">
    
    <script src="https://code.jquery.com/jquery-2.1.3.min.js"></script>
    <script src="https://ajax.googleapis.com/ajax/libs/angularjs/1.3.14/angular.min.js"></script>
    <script src="https://ajax.googleapis.com/ajax/libs/angularjs/1.3.14/angular-sanitize.min.js"></script>
    <script src="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.2/js/bootstrap.min.js"></script>
    
    <script>
        (function(angular) {
            function MainController($scope) {
                $scope.data = %(data)s;
                $scope.model = { activeRow: undefined };
                $scope.search = function (row) {
                    return (angular.lowercase(row.testname).indexOf($scope.query || '') !== -1 || angular.lowercase(row.filename).indexOf($scope.query || '') !== -1);
                };
            }
    
            angular.module('app', ['ngSanitize'])
            .controller('MainController', MainController);
        })(window.angular);
        
        $(function () {
          $('[data-toggle="tooltip"]').tooltip()
        })
    </script>
    </head>
    <body ng-controller="MainController">
        <div class="container-fluid">
            <h3>Balance test report - Generated %(time)s UTC - Version %(version)s</h3>
            Search: <input ng-model="query">
            <div class="table-responsive">
                <table class="table table-hover">
                    <thead>
                    <tr>
                        <th>Name</th>
                        <th>File</th>
                        <th>Groups</th>
                        <th>Expected Winner</th>
                        <th>Cost Effectiveness <span class="glyphicon glyphicon-question-sign" data-toggle="tooltip" title="Damage per cost favouring the winner (positive value) or loser (negative value)."></span></th>
                        <th>Status</th>
                    </tr>
                    </thead>
                    <tbody>
                      <tr ng-repeat-start="entry in data | filter:search" ng-click="model.activeRow = (model.activeRow === entry ? undefined : entry)">
                        <td>{{entry.testname}}</td>
                        <td>{{entry.filename}}</td>
                        <td>{{entry.groups}}</td>
                        <td>{{entry.expectedwinner}}</td>
                        <td ng-bind-html="entry.costeffectiveness"></td>
                        <td ng-class="entry.status === 'Failed' ? 'danger' : 'success'">{{entry.status}}</td>
                      </tr>
                      <tr ng-repeat-end ng-show="entry === model.activeRow">
                            <td></td>
                            <td colspan="5" class="bg-info">
                                <div ng-repeat="info in entry.info">{{info}}</div>
                                <div class="bg-danger" ng-repeat="error in entry.errors"><b>{{error}}</b></div>
                            </td>
                      </tr>
                    </tbody>
                </table>
            </div>
        </div>
    </body>
</html>
'''

outputfolder = 'reports/balance'

def WriteReport(balancetests):
    if not filesystem.FileExists(outputfolder):
        filesystem.CreateDirHierarchy(outputfolder)
        
    data = []
        
    content = ''
    for test in balancetests:
        costeffectiveness = ''
        if test.costeffectiveness:
            for k, v in test.costeffectiveness.items():
                costeffectiveness += '%s: %.2f<br/>' % (k, v)
    
        data.append({
            'testname' : test.testname,
            'filename' : test.filename,
            'groups' : ', '.join(test.groups.keys()),
            'expectedwinner' : test.expectedwinner,
            'costeffectiveness' : costeffectiveness,
            'status' : 'Failed' if test.errors else 'Success',
            'info' : test.info,
            'errors' : test.errors,
        })
        
    params = {
        'data': data,
        'version': srcmgr.DEVVERSION if srcmgr.DEVVERSION else str(srcmgr.VERSION),
        'time': datetime.utcnow(),
    }
    filesystem.WriteFile(os.path.join(outputfolder, 'balancereport.html'), None, htmltemplate % params)