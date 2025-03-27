USE Coapplicant;

CREATE TABLE IF NOT EXISTS `your_table_name` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `coApplicantId` VARCHAR(255),
    `personId` VARCHAR(255),
    `loanId` VARCHAR(255),
    `name` VARCHAR(255),
    `pan` VARCHAR(255),
    `relationToPrimary` VARCHAR(255)
);

INSERT INTO `your_table_name` (`coApplicantId`, `personId`, `loanId`, `name`, `pan`, `relationToPrimary`) VALUES ('C002', 'PERSON001', 'L002', 'Zaitra Subramanian', 'NOHJY6092P', 'Relative');
INSERT INTO `your_table_name` (`coApplicantId`, `personId`, `loanId`, `name`, `pan`, `relationToPrimary`) VALUES ('C004', 'PERSON035', 'L004', 'Ansh Peri', 'NXYGY7241P', 'Friend');
INSERT INTO `your_table_name` (`coApplicantId`, `personId`, `loanId`, `name`, `pan`, `relationToPrimary`) VALUES ('C006', 'PERSON037', 'L006', 'Matthew Jayaraman', 'ZXGDL9073D', 'Sibling');
INSERT INTO `your_table_name` (`coApplicantId`, `personId`, `loanId`, `name`, `pan`, `relationToPrimary`) VALUES ('C007', 'PERSON038', 'L007', 'Urvashi Kapur', 'TONTV1877K', 'Friend');
INSERT INTO `your_table_name` (`coApplicantId`, `personId`, `loanId`, `name`, `pan`, `relationToPrimary`) VALUES ('C018', 'PERSON049', 'L018', 'Damini Brar', 'MZPQE8547Q', 'Parent');
INSERT INTO `your_table_name` (`coApplicantId`, `personId`, `loanId`, `name`, `pan`, `relationToPrimary`) VALUES ('C024', 'PERSON035', 'L024', 'Ansh Peri', 'NXYGY7241P', 'Relative');
INSERT INTO `your_table_name` (`coApplicantId`, `personId`, `loanId`, `name`, `pan`, `relationToPrimary`) VALUES ('C034', 'PERSON045', 'L034', 'Gayathri Varughese', 'OTFDA7574J', 'Spouse');
INSERT INTO `your_table_name` (`coApplicantId`, `personId`, `loanId`, `name`, `pan`, `relationToPrimary`) VALUES ('C035', 'PERSON046', 'L035', 'Isha Yadav', 'SBGLA1964T', 'Sibling');
INSERT INTO `your_table_name` (`coApplicantId`, `personId`, `loanId`, `name`, `pan`, `relationToPrimary`) VALUES ('C036', 'PERSON047', 'L036', 'Yashica Bhardwaj', 'LXPZJ0621F', 'Parent');
INSERT INTO `your_table_name` (`coApplicantId`, `personId`, `loanId`, `name`, `pan`, `relationToPrimary`) VALUES ('C038', 'PERSON049', 'L038', 'Damini Brar', 'MZPQE8547Q', 'Child');
INSERT INTO `your_table_name` (`coApplicantId`, `personId`, `name`, `pan`, `loanId`, `relationToPrimary`) VALUES ('C053', 'PERSON023', 'Thomas Sachdeva', 'DIPJL4437W', 'L053', 'Parent');
INSERT INTO `your_table_name` (`coApplicantId`, `personId`, `name`, `pan`, `loanId`, `relationToPrimary`) VALUES ('C054', 'PERSON038', 'Urvashi Kapur', 'TONTV1877K', 'L054', 'Child');
INSERT INTO `your_table_name` (`coApplicantId`, `personId`, `name`, `pan`, `loanId`, `relationToPrimary`) VALUES ('C059', 'PERSON013', 'Chakradev Soman', 'XXMKZ4355E', 'L059', 'Sibling');
INSERT INTO `your_table_name` (`coApplicantId`, `personId`, `name`, `pan`, `loanId`, `relationToPrimary`) VALUES ('C062', 'PERSON001', 'Zaitra Subramanian', 'NOHJY6092P', 'L062', 'Relative');
INSERT INTO `your_table_name` (`coApplicantId`, `personId`, `name`, `pan`, `loanId`, `relationToPrimary`) VALUES ('C065', 'PERSON009', 'Girik Sur', 'UPJHN9273K', 'L065', 'Parent');
INSERT INTO `your_table_name` (`coApplicantId`, `personId`, `name`, `pan`, `loanId`, `relationToPrimary`) VALUES ('C067', 'PERSON015', 'Meera Jha', 'ITWHB6946I', 'L067', 'Relative');
INSERT INTO `your_table_name` (`coApplicantId`, `personId`, `name`, `pan`, `loanId`, `relationToPrimary`) VALUES ('C068', 'PERSON011', 'Viraj Kar', 'LLALF8573C', 'L068', 'Relative');
INSERT INTO `your_table_name` (`coApplicantId`, `personId`, `name`, `pan`, `loanId`, `relationToPrimary`) VALUES ('C070', 'PERSON005', 'Azad Behl', 'OJTMB3807J', 'L070', 'Child');
INSERT INTO `your_table_name` (`coApplicantId`, `personId`, `name`, `pan`, `loanId`, `relationToPrimary`) VALUES ('C074', 'PERSON009', 'Girik Sur', 'UPJHN9273K', 'L074', 'Parent');
INSERT INTO `your_table_name` (`coApplicantId`, `personId`, `name`, `pan`, `loanId`, `relationToPrimary`) VALUES ('C080', 'PERSON020', 'Panini Saini', 'KHDKX7546N', 'L080', 'Relative');
INSERT INTO `your_table_name` (`coApplicantId`, `personId`, `name`, `pan`, `loanId`, `relationToPrimary`) VALUES ('C081', 'PERSON008', 'Jagat Palan', 'GPLCT9807I', 'L081', 'Child');
INSERT INTO `your_table_name` (`coApplicantId`, `personId`, `name`, `pan`, `loanId`, `relationToPrimary`) VALUES ('C082', 'PERSON019', 'Nachiket Mohan', 'DKWMM4169B', 'L082', 'Parent');
INSERT INTO `your_table_name` (`coApplicantId`, `personId`, `name`, `pan`, `loanId`, `relationToPrimary`) VALUES ('C084', 'PERSON002', 'Balveer Nadkarni', 'IEQYU8992O', 'L084', 'Friend');
INSERT INTO `your_table_name` (`coApplicantId`, `personId`, `name`, `pan`, `loanId`, `relationToPrimary`) VALUES ('C087', 'PERSON015', 'Meera Jha', 'ITWHB6946I', 'L087', 'Friend');
INSERT INTO `your_table_name` (`coApplicantId`, `personId`, `name`, `pan`, `loanId`, `relationToPrimary`) VALUES ('C092', 'PERSON043', 'Chandran Wali', 'CAQZC7665D', 'L092', 'Relative');
INSERT INTO `your_table_name` (`coApplicantId`, `personId`, `loanId`, `name`, `pan`, `relationToPrimary`) VALUES ('C003', 'PERSON034', 'L003', 'Qadim Sood', 'OXXHZ7701C', 'Sibling');
INSERT INTO `your_table_name` (`coApplicantId`, `personId`, `loanId`, `name`, `pan`, `relationToPrimary`) VALUES ('C005', 'PERSON036', 'L005', 'Anita Das', 'HWSAY1083R', 'Spouse');
INSERT INTO `your_table_name` (`coApplicantId`, `personId`, `loanId`, `name`, `pan`, `relationToPrimary`) VALUES ('C008', 'PERSON026', 'L008', 'Neha Mani', 'ZGYOZ7772H', 'Child');
INSERT INTO `your_table_name` (`coApplicantId`, `personId`, `loanId`, `name`, `pan`, `relationToPrimary`) VALUES ('C010', 'PERSON041', 'L010', 'Utkarsh Ramesh', 'XTPHI7971X', 'Sibling');
INSERT INTO `your_table_name` (`coApplicantId`, `personId`, `loanId`, `name`, `pan`, `relationToPrimary`) VALUES ('C012', 'PERSON011', 'L012', 'Viraj Kar', 'LLALF8573C', 'Parent');
INSERT INTO `your_table_name` (`coApplicantId`, `personId`, `loanId`, `name`, `pan`, `relationToPrimary`) VALUES ('C022', 'PERSON009', 'L022', 'Girik Sur', 'UPJHN9273K', 'Parent');
INSERT INTO `your_table_name` (`coApplicantId`, `personId`, `loanId`, `name`, `pan`, `relationToPrimary`) VALUES ('C023', 'PERSON034', 'L023', 'Qadim Sood', 'OXXHZ7701C', 'Parent');
INSERT INTO `your_table_name` (`coApplicantId`, `personId`, `loanId`, `name`, `pan`, `relationToPrimary`) VALUES ('C027', 'PERSON038', 'L027', 'Urvashi Kapur', 'TONTV1877K', 'Child');
INSERT INTO `your_table_name` (`coApplicantId`, `personId`, `loanId`, `name`, `pan`, `relationToPrimary`) VALUES ('C028', 'PERSON039', 'L028', 'Shaurya Atwal', 'KIPVZ6030E', 'Parent');
INSERT INTO `your_table_name` (`coApplicantId`, `personId`, `loanId`, `name`, `pan`, `relationToPrimary`) VALUES ('C029', 'PERSON040', 'L029', 'Ubika Brahmbhatt', 'TVNGE9221L', 'Sibling');
INSERT INTO `your_table_name` (`coApplicantId`, `personId`, `loanId`, `name`, `pan`, `relationToPrimary`) VALUES ('C033', 'PERSON044', 'L033', 'Chakradhar Maharaj', 'ECRWM2471Q', 'Child');
INSERT INTO `your_table_name` (`coApplicantId`, `personId`, `loanId`, `name`, `pan`, `relationToPrimary`) VALUES ('C039', 'PERSON050', 'L039', 'Triveni Nagarajan', 'HTDUU9075J', 'Spouse');
INSERT INTO `your_table_name` (`coApplicantId`, `personId`, `loanId`, `name`, `pan`, `relationToPrimary`) VALUES ('C041', 'PERSON032', 'L041', 'Hemang Goda', 'RJCVY7003D', 'Friend');
INSERT INTO `your_table_name` (`coApplicantId`, `personId`, `loanId`, `name`, `pan`, `relationToPrimary`) VALUES ('C042', 'PERSON033', 'L042', 'Hemangini Nagarajan', 'UONVO1139G', 'Child');
INSERT INTO `your_table_name` (`coApplicantId`, `personId`, `loanId`, `name`, `pan`, `relationToPrimary`) VALUES ('C043', 'PERSON019', 'L043', 'Nachiket Mohan', 'DKWMM4169B', 'Friend');
INSERT INTO `your_table_name` (`coApplicantId`, `personId`, `loanId`, `name`, `pan`, `relationToPrimary`) VALUES ('C044', 'PERSON035', 'L044', 'Ansh Peri', 'NXYGY7241P', 'Spouse');
INSERT INTO `your_table_name` (`coApplicantId`, `personId`, `loanId`, `name`, `pan`, `relationToPrimary`) VALUES ('C050', 'PERSON041', 'L050', 'Utkarsh Ramesh', 'XTPHI7971X', 'Spouse');
INSERT INTO `your_table_name` (`coApplicantId`, `personId`, `name`, `pan`, `loanId`, `relationToPrimary`) VALUES ('C063', 'PERSON043', 'Chandran Wali', 'CAQZC7665D', 'L063', 'Spouse');
INSERT INTO `your_table_name` (`coApplicantId`, `personId`, `name`, `pan`, `loanId`, `relationToPrimary`) VALUES ('C073', 'PERSON003', 'Anvi Raj', 'NWWNS5553J', 'L073', 'Friend');
INSERT INTO `your_table_name` (`coApplicantId`, `personId`, `name`, `pan`, `loanId`, `relationToPrimary`) VALUES ('C075', 'PERSON012', 'Abeer Viswanathan', 'NNUUB5213R', 'L075', 'Friend');
INSERT INTO `your_table_name` (`coApplicantId`, `personId`, `name`, `pan`, `loanId`, `relationToPrimary`) VALUES ('C076', 'PERSON036', 'Anita Das', 'HWSAY1083R', 'L076', 'Relative');
INSERT INTO `your_table_name` (`coApplicantId`, `personId`, `name`, `pan`, `loanId`, `relationToPrimary`) VALUES ('C085', 'PERSON005', 'Azad Behl', 'OJTMB3807J', 'L085', 'Relative');
INSERT INTO `your_table_name` (`coApplicantId`, `personId`, `name`, `pan`, `loanId`, `relationToPrimary`) VALUES ('C091', 'PERSON023', 'Thomas Sachdeva', 'DIPJL4437W', 'L091', 'Friend');
INSERT INTO `your_table_name` (`coApplicantId`, `personId`, `loanId`, `name`, `pan`, `relationToPrimary`) VALUES ('C013', 'PERSON044', 'L013', 'Chakradhar Maharaj', 'ECRWM2471Q', 'Relative');
INSERT INTO `your_table_name` (`coApplicantId`, `personId`, `loanId`, `name`, `pan`, `relationToPrimary`) VALUES ('C015', 'PERSON046', 'L015', 'Isha Yadav', 'SBGLA1964T', 'Child');
INSERT INTO `your_table_name` (`coApplicantId`, `personId`, `loanId`, `name`, `pan`, `relationToPrimary`) VALUES ('C017', 'PERSON048', 'L017', 'Anvi Divan', 'GROZL4615P', 'Relative');
INSERT INTO `your_table_name` (`coApplicantId`, `personId`, `loanId`, `name`, `pan`, `relationToPrimary`) VALUES ('C020', 'PERSON031', 'L020', 'Gunbir Gill', 'JUXHY1719N', 'Sibling');
INSERT INTO `your_table_name` (`coApplicantId`, `personId`, `loanId`, `name`, `pan`, `relationToPrimary`) VALUES ('C021', 'PERSON032', 'L021', 'Hemang Goda', 'RJCVY7003D', 'Parent');
INSERT INTO `your_table_name` (`coApplicantId`, `personId`, `loanId`, `name`, `pan`, `relationToPrimary`) VALUES ('C025', 'PERSON029', 'L025', 'Reva Shah', 'UAKSX0915O', 'Parent');
INSERT INTO `your_table_name` (`coApplicantId`, `personId`, `loanId`, `name`, `pan`, `relationToPrimary`) VALUES ('C026', 'PERSON037', 'L026', 'Matthew Jayaraman', 'ZXGDL9073D', 'Relative');
INSERT INTO `your_table_name` (`coApplicantId`, `personId`, `loanId`, `name`, `pan`, `relationToPrimary`) VALUES ('C030', 'PERSON041', 'L030', 'Utkarsh Ramesh', 'XTPHI7971X', 'Child');
INSERT INTO `your_table_name` (`coApplicantId`, `personId`, `loanId`, `name`, `pan`, `relationToPrimary`) VALUES ('C031', 'PERSON042', 'L031', 'Quincy Dugar', 'LUVFO0785R', 'Spouse');
INSERT INTO `your_table_name` (`coApplicantId`, `personId`, `loanId`, `name`, `pan`, `relationToPrimary`) VALUES ('C037', 'PERSON048', 'L037', 'Anvi Divan', 'GROZL4615P', 'Sibling');
INSERT INTO `your_table_name` (`coApplicantId`, `personId`, `loanId`, `name`, `pan`, `relationToPrimary`) VALUES ('C045', 'PERSON036', 'L045', 'Anita Das', 'HWSAY1083R', 'Sibling');
INSERT INTO `your_table_name` (`coApplicantId`, `personId`, `loanId`, `name`, `pan`, `relationToPrimary`) VALUES ('C048', 'PERSON039', 'L048', 'Shaurya Atwal', 'KIPVZ6030E', 'Parent');
INSERT INTO `your_table_name` (`coApplicantId`, `personId`, `loanId`, `name`, `pan`, `relationToPrimary`) VALUES ('C052', 'PERSON003', 'L052', 'Anvi Raj', 'NWWNS5553J', 'Friend');
INSERT INTO `your_table_name` (`coApplicantId`, `personId`, `name`, `pan`, `loanId`, `relationToPrimary`) VALUES ('C058', 'PERSON003', 'Anvi Raj', 'NWWNS5553J', 'L058', 'Relative');
INSERT INTO `your_table_name` (`coApplicantId`, `personId`, `name`, `pan`, `loanId`, `relationToPrimary`) VALUES ('C061', 'PERSON003', 'Anvi Raj', 'NWWNS5553J', 'L061', 'Spouse');
INSERT INTO `your_table_name` (`coApplicantId`, `personId`, `name`, `pan`, `loanId`, `relationToPrimary`) VALUES ('C066', 'PERSON028', 'Hiral Dash', 'XWGXN4467S', 'L066', 'Parent');
INSERT INTO `your_table_name` (`coApplicantId`, `personId`, `name`, `pan`, `loanId`, `relationToPrimary`) VALUES ('C069', 'PERSON036', 'Anita Das', 'HWSAY1083R', 'L069', 'Parent');
INSERT INTO `your_table_name` (`coApplicantId`, `personId`, `name`, `pan`, `loanId`, `relationToPrimary`) VALUES ('C072', 'PERSON006', 'Vasudha Raj', 'NVZXY1885F', 'L072', 'Spouse');
INSERT INTO `your_table_name` (`coApplicantId`, `personId`, `name`, `pan`, `loanId`, `relationToPrimary`) VALUES ('C077', 'PERSON041', 'Utkarsh Ramesh', 'XTPHI7971X', 'L077', 'Parent');
INSERT INTO `your_table_name` (`coApplicantId`, `personId`, `name`, `pan`, `loanId`, `relationToPrimary`) VALUES ('C079', 'PERSON019', 'Nachiket Mohan', 'DKWMM4169B', 'L079', 'Spouse');
INSERT INTO `your_table_name` (`coApplicantId`, `personId`, `name`, `pan`, `loanId`, `relationToPrimary`) VALUES ('C083', 'PERSON033', 'Hemangini Nagarajan', 'UONVO1139G', 'L083', 'Relative');
INSERT INTO `your_table_name` (`coApplicantId`, `personId`, `name`, `pan`, `loanId`, `relationToPrimary`) VALUES ('C086', 'PERSON004', 'Faras Tara', 'IJCOF0046C', 'L086', 'Spouse');
INSERT INTO `your_table_name` (`coApplicantId`, `personId`, `name`, `pan`, `loanId`, `relationToPrimary`) VALUES ('C088', 'PERSON015', 'Meera Jha', 'ITWHB6946I', 'L088', 'Spouse');
INSERT INTO `your_table_name` (`coApplicantId`, `personId`, `name`, `pan`, `loanId`, `relationToPrimary`) VALUES ('C089', 'PERSON040', 'Ubika Brahmbhatt', 'TVNGE9221L', 'L089', 'Child');
INSERT INTO `your_table_name` (`coApplicantId`, `personId`, `loanId`, `name`, `pan`, `relationToPrimary`) VALUES ('C001', 'PERSON004', 'L001', 'Faras Tara', 'IJCOF0046C', 'Sibling');
INSERT INTO `your_table_name` (`coApplicantId`, `personId`, `loanId`, `name`, `pan`, `relationToPrimary`) VALUES ('C009', 'PERSON040', 'L009', 'Ubika Brahmbhatt', 'TVNGE9221L', 'Parent');
INSERT INTO `your_table_name` (`coApplicantId`, `personId`, `loanId`, `name`, `pan`, `relationToPrimary`) VALUES ('C011', 'PERSON022', 'L011', 'Lila Keer', 'FAYBG7778Z', 'Parent');
INSERT INTO `your_table_name` (`coApplicantId`, `personId`, `loanId`, `name`, `pan`, `relationToPrimary`) VALUES ('C014', 'PERSON045', 'L014', 'Gayathri Varughese', 'OTFDA7574J', 'Friend');
INSERT INTO `your_table_name` (`coApplicantId`, `personId`, `loanId`, `name`, `pan`, `relationToPrimary`) VALUES ('C016', 'PERSON047', 'L016', 'Yashica Bhardwaj', 'LXPZJ0621F', 'Friend');
INSERT INTO `your_table_name` (`coApplicantId`, `personId`, `loanId`, `name`, `pan`, `relationToPrimary`) VALUES ('C019', 'PERSON050', 'L019', 'Triveni Nagarajan', 'HTDUU9075J', 'Friend');
INSERT INTO `your_table_name` (`coApplicantId`, `personId`, `loanId`, `name`, `pan`, `relationToPrimary`) VALUES ('C032', 'PERSON043', 'L032', 'Chandran Wali', 'CAQZC7665D', 'Parent');
INSERT INTO `your_table_name` (`coApplicantId`, `personId`, `loanId`, `name`, `pan`, `relationToPrimary`) VALUES ('C040', 'PERSON014', 'L040', 'Jagvi Thakur', 'BTNVC3285B', 'Parent');
INSERT INTO `your_table_name` (`coApplicantId`, `personId`, `loanId`, `name`, `pan`, `relationToPrimary`) VALUES ('C046', 'PERSON037', 'L046', 'Matthew Jayaraman', 'ZXGDL9073D', 'Spouse');
INSERT INTO `your_table_name` (`coApplicantId`, `personId`, `loanId`, `name`, `pan`, `relationToPrimary`) VALUES ('C047', 'PERSON038', 'L047', 'Urvashi Kapur', 'TONTV1877K', 'Spouse');
INSERT INTO `your_table_name` (`coApplicantId`, `personId`, `loanId`, `name`, `pan`, `relationToPrimary`) VALUES ('C049', 'PERSON040', 'L049', 'Ubika Brahmbhatt', 'TVNGE9221L', 'Friend');
INSERT INTO `your_table_name` (`coApplicantId`, `personId`, `loanId`, `name`, `pan`, `relationToPrimary`) VALUES ('C051', 'PERSON042', 'L051', 'Quincy Dugar', 'LUVFO0785R', 'Friend');
INSERT INTO `your_table_name` (`coApplicantId`, `personId`, `name`, `pan`, `loanId`, `relationToPrimary`) VALUES ('C055', 'PERSON036', 'Anita Das', 'HWSAY1083R', 'L055', 'Parent');
INSERT INTO `your_table_name` (`coApplicantId`, `personId`, `name`, `pan`, `loanId`, `relationToPrimary`) VALUES ('C056', 'PERSON017', 'Logan Desai', 'WTRTG6586A', 'L056', 'Friend');
INSERT INTO `your_table_name` (`coApplicantId`, `personId`, `name`, `pan`, `loanId`, `relationToPrimary`) VALUES ('C057', 'PERSON005', 'Azad Behl', 'OJTMB3807J', 'L057', 'Sibling');
INSERT INTO `your_table_name` (`coApplicantId`, `personId`, `name`, `pan`, `loanId`, `relationToPrimary`) VALUES ('C060', 'PERSON038', 'Urvashi Kapur', 'TONTV1877K', 'L060', 'Friend');
INSERT INTO `your_table_name` (`coApplicantId`, `personId`, `name`, `pan`, `loanId`, `relationToPrimary`) VALUES ('C064', 'PERSON039', 'Shaurya Atwal', 'KIPVZ6030E', 'L064', 'Relative');
INSERT INTO `your_table_name` (`coApplicantId`, `personId`, `name`, `pan`, `loanId`, `relationToPrimary`) VALUES ('C071', 'PERSON002', 'Balveer Nadkarni', 'IEQYU8992O', 'L071', 'Friend');
INSERT INTO `your_table_name` (`coApplicantId`, `personId`, `name`, `pan`, `loanId`, `relationToPrimary`) VALUES ('C078', 'PERSON050', 'Triveni Nagarajan', 'HTDUU9075J', 'L078', 'Parent');
INSERT INTO `your_table_name` (`coApplicantId`, `personId`, `name`, `pan`, `loanId`, `relationToPrimary`) VALUES ('C090', 'PERSON006', 'Vasudha Raj', 'NVZXY1885F', 'L090', 'Friend');
INSERT INTO `your_table_name` (`coApplicantId`, `personId`, `name`, `pan`, `loanId`, `relationToPrimary`) VALUES ('C093', 'PERSON014', 'Jagvi Thakur', 'BTNVC3285B', 'L093', 'Friend');
