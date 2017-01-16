// MODULE
var agentApp = angular.module('agentApp', ['ngRoute', 'ngResource'])

// ROUTES
agentApp.config(function($routeProvider){
  $routeProvider
  .when('/', {
    templateUrl: '/pages/home.html',
    controller: 'homeController as ctrl'
  })
  .when('/creating', {
    templateUrl: '/pages/creating.html',
    controller: 'creatingController as ctrl'
  })
  .when('/info', {
    templateUrl: '/pages/info.html',
    controller: 'infoController as ctrl'
  })
  .when('/modify_pwd', {
    templateUrl: '/pages/modify_pwd.html',
    controller: 'pwdController as ctrl'
  })
  .when('/failed', {
    templateUrl: '/pages/failed.html',
    controller: 'failedController as ctrl'
  })
})

agentApp.config(['$qProvider', function ($qProvider) {
    $qProvider.errorOnUnhandledRejections(false);
}]);


// SERVICES
// ------------ api services defined below ------------

agentApp.service('agentApi', ['$resource', function($resource){
  var status = $resource("/api/status", {}, {get: {method: "GET"}})
  this.getStatus = function() {
    return status.get()
  }

  var appauth_status = $resource("/api/appauth_status", {}, {get: {method: "GET"}})
  this.getAppAuthStatus = function() {
    return appauth_status.get()
  }

  var data_sources = $resource("/api/grafana/data_sources", {}, {post: {method: "POST"}, get: {method: "GET"}})
  this.add_datasource = function(data) {
    return data_sources.post(data)
  }
  this.get_datasource = function() {
    return data_sources.get()
  }

  var data_sources_del = $resource("/api/grafana/data_sources/:id", {}, {"delete": {method: "DELETE"}})
  this.delete_datasource = function(id) {
    return data_sources_del.delete({id:id})
  }

}])

agentApp.service('kirkApi', ['$resource', function($resource){
  var create_app = $resource("/api/kirk/create_app", {}, {post: {method: "POST"}})
  this.create_app = function(data) {
    return create_app.post(data)
  }

  var service_info = $resource("/api/kirk/service_info", {}, {get: {method: "GET"}})
  this.get_service_info = function() {
    return service_info.get()
  }

  var access_addr = $resource("/api/kirk/access_addr", {}, {get: {method: "GET"}})
  this.get_access_addr = function() {
    return access_addr.get()
  }

  var app_list = $resource("/api/kirk/apps", {}, {get: {method: "GET", isArray:true}})
  this.get_app_list = function() {
    return app_list.get()
  }

  var admin_password = $resource("/api/kirk/password", {}, {post: {method:"POST"}})
  this.setPassword = function(pwd) {
    return admin_password.post({"password": pwd})
  }

}])

agentApp.service('configService', function(){
    this.configForm = null
})

// CONTROLLERS
// ------------ home page ------------
agentApp.controller(
  'homeController', 
  [
    '$scope', '$log', '$location',  'agentApi', 'kirkApi', 'configService',
    function($scope, $log, $location, agentApi, kirkApi, configService){
      var self = this

      this.status = agentApi.getStatus()
      this.status.$promise.then(function(data){
        if (data.value === "deployed") {
          $location.path('/info')
        }
        else if (data.value === "failed") {
          $location.path('/failed')
        }
        else if (data.value !== "initialized") {
          console.log(self.status.value)
          $location.path('/creating')
        }
      })

      this.submiting = false

      this.check_pwd = function(){

        if(!this.password || this.password.length < 6) {
          this.errmsg = "密码长度必须在6位以上"
          return
        }

        if(this.password != this.password2) {
          this.errmsg = "两次输入的密码不一致"
          return
        }

        this.errmsg = ""

      }

      this.create_app = function() {

        this.check_pwd()
        if(this.errmsg) {
          return
        }

        this.submiting = true
        configService.configForm = {password: self.password, size: '1U2G'}
        $location.path('/creating')
      }
    }
  ]
)

// ------------ creating page ------------
agentApp.controller(
  'creatingController', 
  [
    '$scope', '$log', '$location', '$interval', 'agentApi', 'kirkApi', 'configService',
    function($scope, $log, $location, $interval, agentApi, kirkApi, configService){
      var self = this
      this.count = 2

      if (configService.configForm) {
        kirkApi.create_app(configService.configForm).$promise.then(function(){
          configService.configForm = null
        })
      }

      // set auto update
      var updateStatus = function() {
        if (self.service_status && self.service_status.status==="RUNNING") {
          $location.path("/info")
        }
        if (self.status && self.status.value==="deployed") {
          self.service_status = kirkApi.get_service_info()
        }
        if (self.status && self.status.value==="failed") {
          $location.path("/failed")
        }
        self.status = agentApi.getStatus()
        self.count = self.count + 1
      }
      updateStatus()
      intvl = $interval(updateStatus, 2000)
      $scope.$on('$destroy', function() {
         $interval.cancel(intvl);
      });
    }
  ]
)

// ------------ info page ------------
agentApp.controller(
  'infoController', 
  [
    '$scope', '$log', '$location',  '$interval', 'agentApi', 'kirkApi', 'configService',
    function($scope, $log, $location, $interval, agentApi, kirkApi, configService){
      var self = this

      // set auto update
      var updateInfo = function() {
        kirkApi.get_service_info().$promise.then(
          function(data){
            self.service_info = data
          }
        )
      }
      updateInfo()
      intvl = $interval(updateInfo, 5000)
      $scope.$on('$destroy', function() {
         $interval.cancel(intvl);
      });

      this.loading = {
        appauth_status: true,
        app_list: true,
        datasources: true,
      }
      this.isLoding = function() {
        for (var key in self.loading) {
          if (self.loading[key]===true){
            return true
          }
        }
        return false
      }

      agentApi.getAppAuthStatus().$promise.then(function(data){
        self.appauth_status = data;
        self.loading.appauth_status = false;
      });
      kirkApi.get_app_list().$promise.then(function(data){
        self.app_list = data;
        self.loading.app_list = false;
      }, function(error){console.log(error);});
      agentApi.get_datasource().$promise.then(function(data){
        self.datasources = data;
        self.loading.datasources = false;
      }, function(error){console.log(error);});
      
      this.access = function(){
        if(self.service_info.status !== "RUNNING") {
          alert("服务尚未运行，请等待服务运行!");
          return;
        }
        kirkApi.get_access_addr().$promise.then(function(data){
          window.open(data.oneTimeUrl, '_blank');
        })
      }

      this.add_datasource = function(appuri) {
        agentApi.add_datasource({appuri:appuri}).$promise.then(function(data){
          window.location.reload();
        }, function(error){
          console.log(error);
        })
      }
      this.alredy_add = function(appuri) {
        if (!self.datasources){
          return false
        }
        for(var i=0; i<self.datasources.data.length; i++){
          if (self.datasources.data[i].name === appuri){
            return true
          }
        }
        return false
      }
      this.delete_datasource = function(appuri) {
        if (!self.datasources) {
          return
        }
        var id = -1;
        for (var i=0; i< self.datasources.data.length; i++) {
          if (self.datasources.data[i].name  === appuri) {
            id = self.datasources.data[i].id;
            break;
          }
        }
        if (id < 0) {
          return
        }

        agentApi.delete_datasource(id).$promise.then(function(data){
          window.location.reload();
        }, function(error){
          console.log(error);
        })
      }

      this.get_status_icon = function() {
        var trans = {
          "RUNNING" : "glyphicon-play",
          "NOT-RUNNING": "glyphicon-stop"
        }

        if (self.service_info) {
          return trans[self.service_info.status]
        }

        return ""
      }

      this.runningTime = function() {
        if (!self.service_info || self.service_info.status !== "RUNNING") {
          return "-"
        }
        var now = new Date();
        var bDay = new Date(self.service_info.updatedAt);
        var elapsedT = now - bDay;
        var secs = elapsedT/1000;
        var minutes = secs / 60;
        var sec = secs % 60;
        var hours = minutes / 60;
        var minute = minutes % 60;
        var hour = hours % 60;
        var day = hours / 12;
        return Math.floor(day) + "天" + Math.floor(hour) +"小时" + Math.floor(minute) + "分钟";
      }

      self.addr = ""
      this.get_access = function(){
        self.addr = "";
        if(self.service_info.status !== "RUNNING") {
          alert("服务尚未运行，请等待服务运行!");
          return;
        }
        kirkApi.get_access_addr().$promise.then(function(data){
          self.addr = data.oneTimeUrl;
        })
      }
    }
  ]
)

// ------------ failed page ------------
agentApp.controller(
  'failedController', 
  [
    '$scope', '$log', '$location', 'agentApi', 'kirkApi', 'configService',
    function($scope, $log, $location, agentApi, kirkApi, configService){
      var self = this
    }
  ]
)

// ------------ pwd set page ------------
agentApp.controller(
  'pwdController', 
  [
    '$scope', '$log', '$location', 'agentApi', 'kirkApi', 'configService',
    function($scope, $log, $location, agentApi, kirkApi, configService){
      var self = this

      this.submit = function() {
        kirkApi.setPassword(self.password).$promise.then(
          function(data){
            $location.path("/info")
          },function(err) {
            alert("设置密码失败!")
          }
        )
      }

      this.check_pwd = function(){
        if(!this.password || this.password.length < 6) {
          this.errmsg = "密码长度必须在6位以上"
          return
        }
        if(this.password != this.password2) {
          this.errmsg = "两次输入的密码不一致"
          return
        }
        this.errmsg = ""
      }

    }
  ]
)
