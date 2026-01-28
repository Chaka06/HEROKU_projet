from django.core.management.base import BaseCommand
from banking.models import Bank


class Command(BaseCommand):
    help = 'Initialise les 30 banques internationales dans la base de données'

    def handle(self, *args, **kwargs):
        banks_data = [
            # Banques Américaines
            {
                'name': 'JPMorgan Chase',
                'country': 'États-Unis',
                'headquarters': 'New York, NY',
                'capital': '920.1 Milliards USD',
                'primary_color': '#117ACA',
                'secondary_color': '#0056A3',
                'accent_color': '#5CA7DB',
                'background_color': '#F0F7FC',
                'text_color': '#FFFFFF',
                'text_dark': '#000000',
                'swift_code': 'CHASUS33',
                'website': 'https://www.jpmorganchase.com',
                'description': 'Plus grande banque américaine par actifs'
            },
            {
                'name': 'Bank of America',
                'country': 'États-Unis',
                'headquarters': 'Charlotte, NC',
                'capital': '424.0 Milliards USD',
                'primary_color': '#012169',
                'secondary_color': '#E31837',
                'text_color': '#FFFFFF',
                'swift_code': 'BOFAUS3N',
                'website': 'https://www.bankofamerica.com',
                'description': 'Deuxième plus grande banque américaine'
            },
            {
                'name': 'Wells Fargo',
                'country': 'États-Unis',
                'headquarters': 'San Francisco, CA',
                'capital': '308.8 Milliards USD',
                'primary_color': '#D71E28',
                'secondary_color': '#FFCD41',
                'text_color': '#FFFFFF',
                'swift_code': 'WFBIUS6S',
                'website': 'https://www.wellsfargo.com',
                'description': 'Banque multinationale de services financiers'
            },
            {
                'name': 'Citibank',
                'country': 'États-Unis',
                'headquarters': 'New York, NY',
                'capital': '225.5 Milliards USD',
                'primary_color': '#003F72',
                'secondary_color': '#ED1C24',
                'text_color': '#FFFFFF',
                'swift_code': 'CITIUS33',
                'website': 'https://www.citibank.com',
                'description': 'Quatrième plus grande banque des États-Unis'
            },
            {
                'name': 'Goldman Sachs',
                'country': 'États-Unis',
                'headquarters': 'New York, NY',
                'capital': '289.2 Milliards USD',
                'primary_color': '#5596E6',
                'secondary_color': '#003D73',
                'text_color': '#FFFFFF',
                'swift_code': 'GSCMUS33',
                'website': 'https://www.goldmansachs.com',
                'description': 'Banque d\'investissement internationale'
            },
            {
                'name': 'Morgan Stanley',
                'country': 'États-Unis',
                'headquarters': 'New York, NY',
                'capital': '299.7 Milliards USD',
                'primary_color': '#00A1DE',
                'secondary_color': '#003D6A',
                'text_color': '#FFFFFF',
                'swift_code': 'MSINUS33',
                'website': 'https://www.morganstanley.com',
                'description': 'Leader en gestion de patrimoine'
            },
            {
                'name': 'Capital One',
                'country': 'États-Unis',
                'headquarters': 'McLean, VA',
                'capital': '165.0 Milliards USD',
                'primary_color': '#004879',
                'secondary_color': '#DA291C',
                'text_color': '#FFFFFF',
                'swift_code': 'HIBKUS44',
                'website': 'https://www.capitalone.com',
                'description': 'Spécialisée dans les cartes de crédit'
            },
            
            # Banques Chinoises
            {
                'name': 'ICBC',
                'country': 'Chine',
                'headquarters': 'Beijing',
                'capital': '353.4 Milliards USD',
                'primary_color': '#C8161D',
                'secondary_color': '#8B0000',
                'text_color': '#FFFFFF',
                'swift_code': 'ICBKCNBJ',
                'website': 'https://www.icbc.com.cn',
                'description': 'Plus grande banque mondiale par actifs'
            },
            {
                'name': 'China Construction Bank',
                'country': 'Chine',
                'headquarters': 'Beijing',
                'capital': '338.5 Milliards USD',
                'primary_color': '#003F87',
                'secondary_color': '#0051A5',
                'text_color': '#FFFFFF',
                'swift_code': 'PCBCCNBJ',
                'website': 'https://www.ccb.com',
                'description': 'Deuxième plus grande banque de Chine'
            },
            {
                'name': 'Agricultural Bank of China',
                'country': 'Chine',
                'headquarters': 'Beijing',
                'capital': '375.2 Milliards USD',
                'primary_color': '#00823B',
                'secondary_color': '#006633',
                'text_color': '#FFFFFF',
                'swift_code': 'ABOCCNBJ',
                'website': 'https://www.abchina.com',
                'description': 'Troisième plus grande banque de Chine'
            },
            {
                'name': 'Bank of China',
                'country': 'Chine',
                'headquarters': 'Beijing',
                'capital': '256.4 Milliards USD',
                'primary_color': '#C8161D',
                'secondary_color': '#8B0000',
                'text_color': '#FFFFFF',
                'swift_code': 'BKCHCNBJ',
                'website': 'https://www.boc.cn',
                'description': 'Quatrième plus grande banque de Chine'
            },
            
            # Banques Européennes
            {
                'name': 'HSBC',
                'country': 'Royaume-Uni',
                'headquarters': 'Londres',
                'capital': '281.8 Milliards USD',
                'primary_color': '#DB0011',
                'secondary_color': '#A00000',
                'accent_color': '#231F20',
                'background_color': '#F5F5F5',
                'text_color': '#FFFFFF',
                'text_dark': '#231F20',
                'swift_code': 'HSBCGB2L',
                'website': 'https://www.hsbc.com',
                'description': 'Banque et services financiers internationaux'
            },
            {
                'name': 'BNP Paribas',
                'country': 'France',
                'headquarters': 'Paris',
                'capital': '105.4 Milliards USD',
                'primary_color': '#009464',
                'secondary_color': '#007348',
                'accent_color': '#39A87B',
                'background_color': '#F0F8F5',
                'text_color': '#FFFFFF',
                'text_dark': '#000000',
                'swift_code': 'BNPAFRPP',
                'website': 'https://www.bnpparibas.com',
                'description': 'Première banque de la zone euro'
            },
            {
                'name': 'Crédit Agricole',
                'country': 'France',
                'headquarters': 'Paris',
                'capital': '95.0 Milliards USD',
                'primary_color': '#009B9D',
                'secondary_color': '#006F4E',
                'text_color': '#FFFFFF',
                'swift_code': 'AGRIFRPP',
                'website': 'https://www.credit-agricole.com',
                'description': 'Leader bancaire mutualiste en France'
            },
            {
                'name': 'Société Générale',
                'country': 'France',
                'headquarters': 'Paris',
                'capital': '85.0 Milliards USD',
                'primary_color': '#E9041E',
                'secondary_color': '#000000',
                'text_color': '#FFFFFF',
                'swift_code': 'SOGEFRPP',
                'website': 'https://www.societegenerale.com',
                'description': 'Banque universelle française'
            },
            {
                'name': 'Banco Santander',
                'country': 'Espagne',
                'headquarters': 'Madrid',
                'capital': '176.4 Milliards USD',
                'primary_color': '#EC0000',
                'secondary_color': '#CC0000',
                'text_color': '#FFFFFF',
                'swift_code': 'BSCHESMM',
                'website': 'https://www.santander.com',
                'description': 'Plus grande banque de la zone euro'
            },
            {
                'name': 'BBVA',
                'country': 'Espagne',
                'headquarters': 'Madrid',
                'capital': '133.1 Milliards USD',
                'primary_color': '#004481',
                'secondary_color': '#0073C9',
                'text_color': '#FFFFFF',
                'swift_code': 'BBVAESMM',
                'website': 'https://www.bbva.com',
                'description': 'Deuxième banque espagnole'
            },
            {
                'name': 'Deutsche Bank',
                'country': 'Allemagne',
                'headquarters': 'Frankfurt',
                'capital': '90.0 Milliards USD',
                'primary_color': '#0018A8',
                'secondary_color': '#00A3E0',
                'text_color': '#FFFFFF',
                'swift_code': 'DEUTDEFF',
                'website': 'https://www.db.com',
                'description': 'Plus grande banque allemande'
            },
            {
                'name': 'ING Group',
                'country': 'Pays-Bas',
                'headquarters': 'Amsterdam',
                'capital': '78.0 Milliards USD',
                'primary_color': '#FF6200',
                'secondary_color': '#172B53',
                'text_color': '#FFFFFF',
                'swift_code': 'INGBNL2A',
                'website': 'https://www.ing.com',
                'description': 'Banque et services financiers néerlandais'
            },
            {
                'name': 'UBS',
                'country': 'Suisse',
                'headquarters': 'Zurich',
                'capital': '148.9 Milliards USD',
                'primary_color': '#E60000',
                'secondary_color': '#8B0000',
                'text_color': '#FFFFFF',
                'swift_code': 'UBSWCHZH',
                'website': 'https://www.ubs.com',
                'description': 'Plus grande banque suisse'
            },
            {
                'name': 'UniCredit',
                'country': 'Italie',
                'headquarters': 'Milan',
                'capital': '125.0 Milliards USD',
                'primary_color': '#E30613',
                'secondary_color': '#000000',
                'text_color': '#FFFFFF',
                'swift_code': 'UNCRITM1',
                'website': 'https://www.unicredit.it',
                'description': 'Groupe bancaire paneuropéen'
            },
            {
                'name': 'Intesa Sanpaolo',
                'country': 'Italie',
                'headquarters': 'Turin',
                'capital': '121.6 Milliards USD',
                'primary_color': '#003366',
                'secondary_color': '#00539F',
                'text_color': '#FFFFFF',
                'swift_code': 'BCITITMM',
                'website': 'https://www.intesasanpaolo.com',
                'description': 'Première banque italienne'
            },
            
            # Banques Canadiennes
            {
                'name': 'Royal Bank of Canada',
                'country': 'Canada',
                'headquarters': 'Toronto',
                'capital': '239.4 Milliards USD',
                'primary_color': '#005DAA',
                'secondary_color': '#FFD520',
                'text_color': '#FFFFFF',
                'swift_code': 'ROYCCAT2',
                'website': 'https://www.rbc.com',
                'description': 'Plus grande banque canadienne'
            },
            {
                'name': 'Toronto-Dominion Bank',
                'country': 'Canada',
                'headquarters': 'Toronto',
                'capital': '162.0 Milliards USD',
                'primary_color': '#00843D',
                'secondary_color': '#005826',
                'text_color': '#FFFFFF',
                'swift_code': 'TDOMCATTTOR',
                'website': 'https://www.td.com',
                'description': 'Deuxième banque canadienne'
            },
            
            # Banques Japonaises
            {
                'name': 'Mitsubishi UFJ Financial',
                'country': 'Japon',
                'headquarters': 'Tokyo',
                'capital': '188.2 Milliards USD',
                'primary_color': '#E60012',
                'secondary_color': '#000000',
                'text_color': '#FFFFFF',
                'swift_code': 'BOTKJPJT',
                'website': 'https://www.mufg.jp',
                'description': 'Plus grand groupe financier japonais'
            },
            {
                'name': 'Sumitomo Mitsui Financial',
                'country': 'Japon',
                'headquarters': 'Tokyo',
                'capital': '128.1 Milliards USD',
                'primary_color': '#00923F',
                'secondary_color': '#005826',
                'text_color': '#FFFFFF',
                'swift_code': 'SMBCJPJT',
                'website': 'https://www.smfg.co.jp',
                'description': 'Deuxième groupe bancaire japonais'
            },
            
            # Banques Indiennes
            {
                'name': 'HDFC Bank',
                'country': 'Inde',
                'headquarters': 'Mumbai',
                'capital': '171.4 Milliards USD',
                'primary_color': '#004C8F',
                'secondary_color': '#ED1C24',
                'text_color': '#FFFFFF',
                'swift_code': 'HDFCINBB',
                'website': 'https://www.hdfcbank.com',
                'description': 'Plus grande banque privée indienne'
            },
            {
                'name': 'ICICI Bank',
                'country': 'Inde',
                'headquarters': 'Mumbai',
                'capital': '111.8 Milliards USD',
                'primary_color': '#F37021',
                'secondary_color': '#522E91',
                'text_color': '#FFFFFF',
                'swift_code': 'ICICINBB',
                'website': 'https://www.icicibank.com',
                'description': 'Deuxième banque privée indienne'
            },
            {
                'name': 'State Bank of India',
                'country': 'Inde',
                'headquarters': 'Mumbai',
                'capital': '103.8 Milliards USD',
                'primary_color': '#22409A',
                'secondary_color': '#1E3A8A',
                'text_color': '#FFFFFF',
                'swift_code': 'SBININBB',
                'website': 'https://www.sbi.co.in',
                'description': 'Plus grande banque indienne'
            },
            
            # Autres Banques Internationales
            {
                'name': 'DBS Group',
                'country': 'Singapour',
                'headquarters': 'Singapour',
                'capital': '129.3 Milliards USD',
                'primary_color': '#DC1431',
                'secondary_color': '#8B0A1A',
                'text_color': '#FFFFFF',
                'swift_code': 'DBSSSGSG',
                'website': 'https://www.dbs.com',
                'description': 'Plus grande banque d\'Asie du Sud-Est'
            },
            {
                'name': 'Commonwealth Bank',
                'country': 'Australie',
                'headquarters': 'Sydney',
                'capital': '173.0 Milliards USD',
                'primary_color': '#FFCC00',
                'secondary_color': '#000000',
                'text_color': '#000000',
                'swift_code': 'CTBAAU2S',
                'website': 'https://www.commbank.com.au',
                'description': 'Plus grande banque australienne'
            },
            {
                'name': 'Al Rajhi Bank',
                'country': 'Arabie Saoudite',
                'headquarters': 'Riyadh',
                'capital': '105.3 Milliards USD',
                'primary_color': '#006747',
                'secondary_color': '#004D34',
                'text_color': '#FFFFFF',
                'swift_code': 'RJHISARI',
                'website': 'https://www.alrajhibank.com.sa',
                'description': 'Plus grande banque islamique au monde'
            },
            {
                'name': 'Barclays',
                'country': 'Royaume-Uni',
                'headquarters': 'Londres',
                'capital': '95.0 Milliards USD',
                'primary_color': '#00AEEF',
                'secondary_color': '#003D4C',
                'text_color': '#FFFFFF',
                'swift_code': 'BARCGB22',
                'website': 'https://www.barclays.co.uk',
                'description': 'Banque britannique multinationale'
            },
            {
                'name': 'Standard Chartered',
                'country': 'Royaume-Uni',
                'headquarters': 'Londres',
                'capital': '75.0 Milliards USD',
                'primary_color': '#007A33',
                'secondary_color': '#004D20',
                'text_color': '#FFFFFF',
                'swift_code': 'SCBLGB2L',
                'website': 'https://www.sc.com',
                'description': 'Banque britannique en Asie, Afrique et Moyen-Orient'
            },
            {
                'name': 'Scotiabank',
                'country': 'Canada',
                'headquarters': 'Toronto',
                'capital': '88.0 Milliards USD',
                'primary_color': '#EC1C24',
                'secondary_color': '#000000',
                'text_color': '#FFFFFF',
                'swift_code': 'NOSCCATT',
                'website': 'https://www.scotiabank.com',
                'description': 'Troisième banque canadienne'
            },
            {
                'name': 'Lloyds Banking Group',
                'country': 'Royaume-Uni',
                'headquarters': 'Londres',
                'capital': '72.0 Milliards USD',
                'primary_color': '#006638',
                'secondary_color': '#004D2A',
                'text_color': '#FFFFFF',
                'swift_code': 'LOYDGB2L',
                'website': 'https://www.lloydsbankinggroup.com',
                'description': 'Groupe bancaire britannique majeur'
            },
            {
                'name': 'China Merchants Bank',
                'country': 'Chine',
                'headquarters': 'Shenzhen',
                'capital': '166.6 Milliards USD',
                'primary_color': '#ED1B2E',
                'secondary_color': '#8B0A1A',
                'text_color': '#FFFFFF',
                'swift_code': 'CMBCCNBS',
                'website': 'https://www.cmbchina.com',
                'description': 'Banque commerciale chinoise'
            },
            {
                'name': 'Westpac',
                'country': 'Australie',
                'headquarters': 'Sydney',
                'capital': '65.0 Milliards USD',
                'primary_color': '#DA1710',
                'secondary_color': '#8B0A0A',
                'text_color': '#FFFFFF',
                'swift_code': 'WPACAU2S',
                'website': 'https://www.westpac.com.au',
                'description': 'Deuxième banque australienne'
            },
            {
                'name': 'ANZ',
                'country': 'Australie',
                'headquarters': 'Melbourne',
                'capital': '62.0 Milliards USD',
                'primary_color': '#007CB0',
                'secondary_color': '#003D5C',
                'text_color': '#FFFFFF',
                'swift_code': 'ANZBAU3M',
                'website': 'https://www.anz.com.au',
                'description': 'Banque australienne et néo-zélandaise'
            },
            {
                'name': 'Nordea',
                'country': 'Finlande',
                'headquarters': 'Helsinki',
                'capital': '55.0 Milliards USD',
                'primary_color': '#0000A0',
                'secondary_color': '#00008B',
                'text_color': '#FFFFFF',
                'swift_code': 'NDEAFIHH',
                'website': 'https://www.nordea.com',
                'description': 'Plus grand groupe bancaire nordique'
            },
            {
                'name': 'Credit Suisse',
                'country': 'Suisse',
                'headquarters': 'Zurich',
                'capital': '50.0 Milliards USD',
                'primary_color': '#003D7A',
                'secondary_color': '#001F3D',
                'text_color': '#FFFFFF',
                'swift_code': 'CRESCHZZ',
                'website': 'https://www.credit-suisse.com',
                'description': 'Groupe bancaire suisse international'
            },
            {
                'name': 'Mizuho Financial Group',
                'country': 'Japon',
                'headquarters': 'Tokyo',
                'capital': '95.0 Milliards USD',
                'primary_color': '#004A9C',
                'secondary_color': '#002855',
                'text_color': '#FFFFFF',
                'swift_code': 'MHCBJPJT',
                'website': 'https://www.mizuhogroup.com',
                'description': 'Troisième groupe bancaire japonais'
            },
            {
                'name': 'Rabobank',
                'country': 'Pays-Bas',
                'headquarters': 'Utrecht',
                'capital': '48.0 Milliards USD',
                'primary_color': '#FF6200',
                'secondary_color': '#003D6D',
                'text_color': '#FFFFFF',
                'swift_code': 'RABONL2U',
                'website': 'https://www.rabobank.com',
                'description': 'Banque coopérative néerlandaise'
            },
            {
                'name': 'National Bank of Canada',
                'country': 'Canada',
                'headquarters': 'Montréal',
                'capital': '42.0 Milliards USD',
                'primary_color': '#D71920',
                'secondary_color': '#8B0000',
                'text_color': '#FFFFFF',
                'swift_code': 'BNDCCAMMINT',
                'website': 'https://www.nbc.ca',
                'description': 'Sixième banque canadienne'
            },
            {
                'name': 'BMO Bank of Montreal',
                'country': 'Canada',
                'headquarters': 'Montréal',
                'capital': '85.0 Milliards USD',
                'primary_color': '#0075C9',
                'secondary_color': '#003D6D',
                'text_color': '#FFFFFF',
                'swift_code': 'BOFMCAM2',
                'website': 'https://www.bmo.com',
                'description': 'Plus ancienne banque du Canada'
            },
            {
                'name': 'Standard Bank',
                'country': 'Afrique du Sud',
                'headquarters': 'Johannesburg',
                'capital': '38.0 Milliards USD',
                'primary_color': '#003087',
                'secondary_color': '#001B4D',
                'text_color': '#FFFFFF',
                'swift_code': 'SBZAZAJJ',
                'website': 'https://www.standardbank.com',
                'description': 'Plus grande banque africaine'
            },
            {
                'name': 'Qatar National Bank',
                'country': 'Qatar',
                'headquarters': 'Doha',
                'capital': '65.0 Milliards USD',
                'primary_color': '#68166C',
                'secondary_color': '#3D0A3F',
                'text_color': '#FFFFFF',
                'swift_code': 'QNBAQAQA',
                'website': 'https://www.qnb.com',
                'description': 'Plus grande banque du Moyen-Orient'
            },
            {
                'name': 'First Abu Dhabi Bank',
                'country': 'Émirats Arabes Unis',
                'headquarters': 'Abu Dhabi',
                'capital': '55.0 Milliards USD',
                'primary_color': '#004A98',
                'secondary_color': '#002855',
                'text_color': '#FFFFFF',
                'swift_code': 'NBADAEAA',
                'website': 'https://www.bankfab.com',
                'description': 'Plus grande banque des EAU'
            },
            {
                'name': 'Banco do Brasil',
                'country': 'Brésil',
                'headquarters': 'Brasília',
                'capital': '45.0 Milliards USD',
                'primary_color': '#FFCC00',
                'secondary_color': '#003D7A',
                'text_color': '#003D7A',
                'swift_code': 'BRASBRRJ',
                'website': 'https://www.bb.com.br',
                'description': 'Plus grande banque d\'Amérique latine'
            },
            {
                'name': 'Itaú Unibanco',
                'country': 'Brésil',
                'headquarters': 'São Paulo',
                'capital': '52.0 Milliards USD',
                'primary_color': '#EC7000',
                'secondary_color': '#003D7A',
                'text_color': '#FFFFFF',
                'swift_code': 'ITAUBRSP',
                'website': 'https://www.itau.com.br',
                'description': 'Plus grande banque privée du Brésil'
            },
            {
                'name': 'Banco Bradesco',
                'country': 'Brésil',
                'headquarters': 'Osasco',
                'capital': '38.0 Milliards USD',
                'primary_color': '#CC092F',
                'secondary_color': '#8B0000',
                'text_color': '#FFFFFF',
                'swift_code': 'BBDEBRSP',
                'website': 'https://www.bradesco.com.br',
                'description': 'Deuxième banque privée du Brésil'
            },
        ]

        created_count = 0
        updated_count = 0

        for bank_data in banks_data:
            bank, created = Bank.objects.get_or_create(
                name=bank_data['name'],
                defaults=bank_data
            )
            
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'✓ Banque créée: {bank.name}'))
            else:
                # Mettre à jour les données si la banque existe déjà
                for key, value in bank_data.items():
                    setattr(bank, key, value)
                bank.save()
                updated_count += 1
                self.stdout.write(self.style.WARNING(f'→ Banque mise à jour: {bank.name}'))

        self.stdout.write(self.style.SUCCESS(f'\n✓ Terminé! {created_count} banques créées, {updated_count} mises à jour.'))
        self.stdout.write(self.style.SUCCESS(f'Total: {Bank.objects.count()} banques dans la base de données.'))
