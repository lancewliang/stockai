from load_data import PrepareData
from data_preprocessing import DataPreProcess
from train_wgan import WGANGPTrainer
from test_trading import TraderTest
number = "000002"
root = "/home/lanceliang/cdpwork/ai/ai-stock/stockai/"
_PrepareData = PrepareData()
_PrepareData.do_prepare(number,root)

_DataPreProcess = DataPreProcess()
_DataPreProcess.doProcess(number,root)

_WGANGPTrainer = WGANGPTrainer()
_WGANGPTrainer.doProcess(number,root)

_TraderTest = TraderTest()
_TraderTest.doProcess(number,root)