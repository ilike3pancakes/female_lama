admin_from_jid_prefixes = {
    "ilike3pancakes0_",
    "_51n__", # sin

    "c7mjfxiow6r43yxlpxtxuomgddwcj4wkaqdpcgb6lckg3arw6ewq_",  # ilike3pancakes
    "od67rvy7hl5sya76cx2ivacapijhz5apc2kwprgqfxywk3ako6ba_",  # ilike3pancakes

    "xe64nqmzhcjlct2sux64gslxbhjiequmfdrnantyrhy3cz3ulv7q_",  # Adam@BGE
    "saagukw4hkjf32ap7q6yo6qyragkhutqzfdbt4tkbsc3f2ijkrbq_",  # ilike3pancakes@BGE
    "v32t7cqoj3syalzsajcg6szbah3i3p4nxdmnjo6y6nilenur7n3q_",  # Eric@BGE

    "tgd2yc43fejlxduc4aortmiwruolj7rwlnfjk5prenqjdewddhiq_",  # ilike3pancakes@friendzandmusic
    "hmvrgi7tpv5by6qqk252khwednv5zlwxd3kiyuzqrnjjcra67boq_",  # Kat@friendzandmusic
    "wwafkxej3w4hlobauwcyhopmeudw4lfoqr2eqeh7sril6yijouea_",  # wetter@friendzandmusic

    "6gbvbz4budh7yhwxsijjdklyka7klats3bhsh6lh4aspzfywi44q_",  # wetter@coven
    "zkw2ncbf7euiilw4iguwwtkemrhrnpgrqynaa3y7afwhef7mtpoq_",  # ilike3pancakes@coven
    "5hbwwosipuzzpxkp3wsgk24cpcwfck3qg7ounznl4vmzvlgjbwoa_",  # maze@coven

    "2cgtgby2hjsyqf7ec3m6iwkgrn5mmqieaigporcaywhme6t5uncq_",  # Boney@WeeklyGroup
    "xfouihqbab7z4gj22c4tnwczhs42k3jcxfefxv2gjhhlbcqmj56a_",  # ilike3pancakes@WeeklyGroup
    "2zlonhc7h6p4fho5piltyoq2t56j6gkow74tzidugapsdeemumga_",  # Ginger@WeeklyGroup
    "xf6kypcya5xorfnaa27ub5jejhb24wjzy7d5jgrpxfbu7xy6pw4q_",  # Croc@WeeklyGroup
    "j5bbcengkilas7gi5rthcl5z3dg4wskzfqmqbjjoxqda4o4yajsa_",  # TexMex@WeeklyGroup

    "tm4l3a6fczoevkfmqrl6k5v74lwrfmpzkiqtcawoxrlbpmmg556a_",  # sin@labyrinth
    "5ecfkurhvuxs7cr6gcaqon7oj7htpczjwaxlqobtubrcfhusc43a_",  # ilike3pancakes@labyrinth
    "ie7jqalznw7khfnb223x57ijf7euwzcuodgcy4sfvzgztwk4zo3q_",  # Cy@labyrinth
    "vgpgbtp7xfspzw4n545atfrlxo7gpft3yc3rdia3lm6vkgavu2ya_",  # Rusto@labyrinth

    "a6vixtbtqs5dzhv3wxgdli5krb3x67tmdh7h2dm2rhazvpx2mcna_",  # ilike3@booksandfriends
    "b22lutm5y7mxjc57yqygnbgqfhgqhya5z74to56vzb7oykrox6sa_",  # AB@booksandfriends

    "jxlswh5ml6qbkm6ditnwdz6s4itwnz22ugr73nky7mk73zvk3s6a_",  # ilike3@makefriendsandameme

    "hbpz6pb625hv3jvc6ztvnd5bhhcfhn33almsyazv3wlrap4lrbuq_",  # ilike3@booksbant
    "thdjn4x6hpve7jfubqbhurmzjmfud4o6vydsh6ldhgz6bwi447cq_",  # blas@booksban
}


def auth(user_jid: str) -> bool:
    return any(user_jid.startswith(prefix) for prefix in admin_from_jid_prefixes)


if __name__ == "__main__":
    assert auth("ilike3pancakes0_xyz")
    assert not auth("someuser_123")
    print("Ok")
