# generated file
from flopy4.model import MFModel
from flopy4.resolver import Resolve
from spec.ipkg.gwt_dis import GwtDis


class GwtModel(MFModel, Resolve):
    dis6 = GwtDis()
