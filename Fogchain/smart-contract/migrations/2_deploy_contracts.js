var Crowdsale = artifacts.require("./Crowdsale.sol");

module.exports = function(deployer) {
  deployer.deploy(Crowdsale,0x4362179847e991a9e2d38c7874072018305d1e71,250,45000,5,0x693bd784fa53df016083de99bd82f3d94d8487ae);
};
