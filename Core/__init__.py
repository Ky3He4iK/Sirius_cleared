import pandas as pd
from django.conf import settings
import json
import os

_table = pd.read_csv(os.path.join(settings.BASE_DIR, "data/main_table.csv"), sep=';')
_addresses = pd.read_csv(os.path.join(settings.BASE_DIR, "data/addresses.csv"), sep=';')
# coordinates = [{'ekis_id': int(_addresses.ekis_id[ind]), 'fulltext': _addresses.fulltext[ind],
#                 'latLng': [_addresses.lat[ind], _addresses.lng[ind]]}
#                for ind in range(len(_addresses))
#                if str(_addresses['lat'][ind]) != 'nan' and str(_addresses['lng'][ind]) != 'nan']
_profiles = [col[2:] for col in list(_table.columns) if col[:2] == "p_"]
_districts = list(_addresses.okrug.value_counts(dropna=True).reset_index()['index'])  # Magic. .Do not touch!
_forbidden_subject_parts = [" устный", "Математика базовая", "Сочинение"]
_forbidden_subjects = ["EGE_Математика"]
_universities = [col[2:] for col in list(_table.columns) if col[:2] == "В_"]
_universities_transit = {vyz[vyz.rfind(', ') + 1:] if ', ' in vyz else vyz: vyz for vyz in _universities}
_universities_transit_reverse = {vyz: vyz_short for vyz, vyz_short in _universities_transit.items()}


def _to_json(d):
    return json.dumps(d, ensure_ascii=False)


def _check_subj(subj):
    for fb in _forbidden_subject_parts:
        if fb in subj:
            return False
    return subj not in _forbidden_subjects
    # return True


def _addresses_to_arr(tt):
    return [{'ekis_id': int(_addresses.ekis_id[ind]),
             'isMain': bool(tt['main'][ind]), 'name': tt['short_name'][ind],
             'latLng': [float(tt['lat'][ind]), float(tt['lng'][ind])],
             'fullname': str(tt['fulltext'][ind])} for ind in range(len(tt))
            if str(tt['lat'][ind]) != 'nan' and str(tt['lng'][ind]) != 'nan']


_ege = [col[4:] for col in list(_table.columns) if col[:4] == "EGE_" and _check_subj(col)]
_oge = [col[4:] for col in list(_table.columns) if col[:4] == "OGE_" and _check_subj(col)]
coordinates = _addresses_to_arr(_addresses)
coordinates_showing = [coord for coord in coordinates[::2] if coord['isMain']]
lists = {'coordinates': coordinates, 'profiles': _profiles, 'ege': _ege, 'oge': _oge, 'okrugs': _districts,
         'coordinates_showing': coordinates_showing}
lists_json = _to_json(lists)


def _get_school_pair(ekis):
    return int(ekis), str(_table[_table.ekis_id == ekis].reset_index().short_name[0])


def _profiles_to_str(t, ind=0):
    return ', '.join([profile for profile in _profiles if t["p_" + profile][ind] == 1])


def _get_school_short(ekis_id):
    t = _table[_table.ekis_id == ekis_id].reset_index()
    if len(t) != 1:
        return {}
    res = {
        "ekis_id": ekis_id,
        "name": str(t.short_name[0]),
        "profiles": _profiles_to_str(t),
        "legal_address": str(t.legal_address[0]),
        "ou_class": str(t.ou_class[0]),
        "addresses": _addresses_to_arr(_addresses[_addresses.ekis_id == ekis_id].reset_index()),
    }
    return res


def _get_school_short_ind(ind):
    res = {
        "ekis_id": int(_table.ekis_id[ind]),
        "name": str(_table.short_name[ind]),
        "profiles": _profiles_to_str(_table, ind),
        "legal_address": str(_table.legal_address[ind]),
        "ou_class": str(_table.ou_class[ind]),
        "addresses": _addresses_to_arr(_addresses[_addresses.ekis_id == _table.ekis_id[ind]].reset_index()),
    }
    return res


def _get_schools_short_ind(inds):
    return [_get_school_short_ind(ind) for ind in inds]


def _filtering(filters):
    def _filter_by_okrug(names):
        def _has_filial(ind):
            tt = _addresses[_addresses.ekis_id == _table.ekis_id[ind]]
            for okrug in tt.okrug:
                if okrug in names:
                    return True
            return False

        return [ind for ind in inds if _has_filial(ind)]

    def _filter_by_class(number):
        return [ind for ind in range(len(_table)) if _table.min_parallel[ind] <= number <= _table.max_parallel[ind]]

    def _filter_by_profiles(profiles):
        sets = [set([ind for ind in inds if profile in _profiles and _table['p_' + profile][ind] == 1])
                for profile in profiles if profile in _profiles]
        return list(sets[0].intersection(*sets[1:]))

    def _filter_by_ege(ege):
        sets = [set([ind for ind in inds
                     if 'name' in subj and 'min' in subj and 'max' in subj and subj['name'] in _ege
                     and subj['min'] <= _table['EGE_' + subj['name']][ind] <= subj['max']])
                for subj in ege if subj['min'] != 0 or subj['max'] != 100]
        if len(sets) == 0:
            return inds
        return list(sets[0].intersection(*sets[1:]))

    def _filter_by_oge(oge):
        sets = [set([ind for ind in inds
                     if 'name' in subj and 'min' in subj and 'max' in subj and subj['name'] in _oge
                     and subj['min'] <= _table['OGE_' + subj['name']][ind] <= subj['max']])
                for subj in oge if subj['min'] != 2 or subj['max'] != 5]
        if len(sets) == 0:
            return inds
        return list(sets[0].intersection(*sets[1:]))

    if len(filters) == 0:  # special for lazy pasha 'cause he can't use /api/get_lists
        return list(range(len(_table)))

    if 'parallel' in filters:
        inds = _filter_by_class(filters['parallel'])
    else:
        inds = range(len(_table))
    if 'profiles' in filters and len(filters['profiles']) > 0:
        inds = _filter_by_profiles(filters['profiles'])
    if 'ege' in filters and len(filters['ege']) > 0:
        inds = _filter_by_ege(filters['ege'])
    if 'oge' in filters and len(filters['oge']) > 0:
        inds = _filter_by_oge(filters['oge'])
    if 'okrugs' in filters and len(_districts) > len(filters['okrugs']) > 0:
        inds = _filter_by_okrug(filters['okrugs'])
    return inds


# get top 10 vuzes for this ekis_id
# t is dataframe with one string (this ekis_id), columns are vuzes
def _get_top_vyzes(t):
    new_t = t.fillna(0)
    d = {}
    for i in _universities:
        d[i] = round(new_t.at[0, 'В_' + i], 2)
    d_sorted = sorted(d.items(), key=lambda kv: kv[1])
    return d_sorted[-10:][::-1]


def get_school(ekis_id):
    t = _table[_table.ekis_id == ekis_id].reset_index()
    if len(t) != 1:
        return {}
    res = {
        "name": str(t.short_name[0]),
        "name_full": str(t.name[0]),
        "site": str(t.site[0]),
        "email": str(t.email[0]),
        "principal": str(t.principal[0]),
        "stud_from": str(t.min_parallel[0]),
        "stud_to": str(t.max_parallel[0]),
        "profiles": _profiles_to_str(t),
        "legal_address": str(t.legal_address[0]),
        "financing": str(t.financing[0]),
        "ogrn": str(t.ogrn[0]),
        "okato": str(t.okato[0]),
        "ou_class": str(t.ou_class[0]),
        "subjects_ege": {subj: round(float(t["EGE_" + subj][0]), 2) for subj in _ege if str(t["EGE_" + subj][0]) != 'nan'
                         and int(t["EGE_" + subj][0]) != 0},
        "subjects_oge": {subj: round(float(t["OGE_" + subj][0]), 2) for subj in _oge if str(t["OGE_" + subj][0]) != 'nan'
                         and int(t["OGE_" + subj][0]) != 0},
        "addresses": _addresses_to_arr(_addresses[_addresses.ekis_id == ekis_id].reset_index()),
        "schools_like_this": [_get_school_pair(t['Schools_Like_This_' + str(i)][0]) for i in range(1, 11)],
        "top_vyzes": _get_top_vyzes(t.loc[:, ['В_' + vyz for vyz in _universities]].fillna(0))
    }
    res['has_ege'] = len(res['subjects_ege']) > 0
    res['has_oge'] = len(res['subjects_oge']) > 0
    res['has_vyzes'] = bool(res['top_vyzes'][0][1] > 0)
    return res


def get_schools_by_string(string):
    res = []
    clear_string = ''
    for i in string:
        if i.isalpha() or i.isdigit():
            clear_string += i
        else:
            clear_string += ' '
    words = clear_string.lower().split()
    for i, name in enumerate(_table.short_name + ' ' + _table.name):
        isIn = True
        for word in words:
            if not (word in str(name).lower()):
                isIn = False
        if isIn:
            res.append(_get_school_short_ind(i))
    return res


def get_schools_filter(filters):
    """
    {
      "okrugs": [
        "Северо-Восточный",
        "Троицкий"
      ],
      "egeResults": [
        {
          "max": 78,
          "min": 26,
          "name": "Математика (профиль)"
        }
      ],
      "ogeResults": [
        {
          "max": 5,
          "min": 2,
          "name": "Математика"
        }
      ],
      "parallel": "10",
      "profiles": [
        "Естественно-научный",
        "Экономический"
      ]
    }
    """
    return _get_schools_short_ind(_filtering(filters))


def get_school_json(ekis_id):
    return _to_json(get_school(ekis_id))


def get_schools_by_string_json(string):
    return _to_json(get_schools_by_string(string))


def get_schools_filter_json(filters):
    return _to_json(get_schools_filter(filters))


def get_lists():
    return lists_json
