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
  .when('/failed', {
    templateUrl: '/pages/failed.html',
    controller: 'failedController as ctrl'
  })
})

agentApp.config(['$qProvider', function ($qProvider) {
    $qProvider.errorOnUnhandledRejections(false);
}]);


// SERVICES
agentApp.service('agentApi', ['$resource', function($resource){
  var status = $resource("/api/status", {}, {get: {method: "GET"}})
  this.getStatus = function() {
    return status.get()
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
}])

agentApp.service('configService', function(){
    this.configForm = null
})

// CONTROLLERS
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
        if (data.value === "failed") {
          $location.path('/failed')
        }
        if (data.value !== "initialized") {
          console.log(self.status.value)
          $location.path('/creating')
        }
      })

      this.sizes = ['1U1G', '1U2G', '2U2G', '2U4G', '4U8G', '4U16G']
      this.size = '1U2G'
      this.instanceNum = 1
      this.create_app = function() {
        configService.configForm = {password: self.password, size: self.size, instanceNum: self.instanceNum}
        $location.path('/creating')
      }
    }
  ]
)

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
        if (self.status && self.status.value==="deployed") {
          $location.path("/info")
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

agentApp.controller(
  'infoController', 
  [
    '$scope', '$log', '$location',  'agentApi', 'kirkApi', 'configService',
    function($scope, $log, $location, agentApi, kirkApi, configService){
      var self = this
      this.service_info = kirkApi.get_service_info()
      
      this.access = function(){
        kirkApi.get_access_addr().$promise.then(function(data){
          window.open(data.oneTimeUrl, '_blank');
        })
      }
    }
  ]
)

agentApp.controller(
  'failedController', 
  [
    '$scope', '$log', '$location',  'agentApi', 'kirkApi', 'configService',
    function($scope, $log, $location, agentApi, kirkApi, configService){
      var self = this
    }
  ]
)
