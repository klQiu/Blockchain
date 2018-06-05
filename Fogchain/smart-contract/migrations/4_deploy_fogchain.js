var Fogchain = artifacts.require("./Fogchain_2.sol");

module.exports = function(deployer) {
  //params: (uint seq_blk_interval, uint renew_price, uint unre_price) 
  deployer.deploy(Fogchain, 10, 800, 1000);
};
